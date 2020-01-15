/* module.h - Valhalla Tracker (libvht)
 *
 * Copyright (C) 2019 Remigiusz Dybka - remigiusz.dybka@gmail.com
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <stdio.h>
#include <math.h>
#include <pthread.h>
#include "module.h"
#include "midi_client.h"
#include "track.h"
#include "midi_event.h"

struct rec_update_t rec_update[MIDI_EVT_BUFFER_LENGTH];
int cur_rec_update;

int lastsec;

void module_excl_in(module *mod) {
	pthread_mutex_lock(&mod->excl);
}

void module_excl_out(module *mod) {
	pthread_mutex_unlock(&mod->excl);
}

// the GOD function
void module_advance(module *mod, jack_nframes_t curr_frames) {
	if (mod->nseq == 0)
		return;

	module_excl_in(mod);

	midi_buffer_clear(mod->clt);

	if (!mod->playing) {
		// are we paused?
		if (mod->zero_time > 0)
			mod->zero_time += mod->clt->jack_buffer_size;
	}

	// are we muting after stop?
	if (!mod->playing && mod->mute) {
		for (int t = 0; t < mod->seq[mod->curr_seq]->ntrk; t++)
			track_kill_notes(mod->seq[mod->curr_seq]->trk[t]);

		mod->mute = 0;
	}

	if (mod->zero_time == 0)
		mod->zero_time = curr_frames;

	double time = (curr_frames - mod->zero_time) / (double)mod->clt->jack_sample_rate;
	double row_length = 60.0 / ((double)mod->rpb * (double)mod->bpm);
	double period = ((double)mod->clt->jack_buffer_size / (double)mod->clt->jack_sample_rate) / row_length;

	mod->sec = time;
	mod->min = mod->sec / 60;
	mod->sec -= (mod->min * 60);

	mod->ms = (time - floorf(time)) * 1000;

	if (mod->playing) {
		// play mode and stuff will go here later
		sequence *seq = mod->seq[0];
		sequence_advance(seq, period);
		timeline_advance(mod->tline, period);
	}

// handle input from MIDI
	void *inp = jack_port_get_buffer(mod->clt->jack_input_port, mod->clt->jack_buffer_size);

	jack_nframes_t ninp;
	jack_midi_event_t evt;

	ninp = jack_midi_get_event_count(inp);

	int empty = 0;

	for (jack_nframes_t n = 0; (n < ninp) && !empty; n++) {
		empty = jack_midi_event_get(&evt, inp, n);
		if (!empty) {
			midi_event mev = midi_decode_event(evt.buffer, evt.size);
			mev.time = evt.time;

			if (!mod->recording) {
				midi_buffer_add(mod->clt, mod->clt->default_midi_port, mev);
			}

			midi_in_buffer_add(mod->clt, mev);

			int ignore = 0;

			midi_ignore_buff_excl_in(mod->clt);
			for (int f = 0; f < mod->clt->curr_midi_ignore_event; f++) {
				midi_event ignev = mod->clt->midi_ignore_buffer[f];
				if (ignev.channel == mev.channel)
					if (ignev.type == mev.type)
						if (ignev.note == mev.note)
							ignore = 1;
			}

			midi_ignore_buff_excl_out(mod->clt);

			if (mod->recording && !ignore) {
				sequence_handle_record(mod, mod->seq[mod->curr_seq], mev);
			}
		}
	}

	//printf("time: %02d:%02d:%03d %3.5f %d\n", module.min, module.sec, module.ms, period, module.bpm);
	mod->song_pos += period;
	module_excl_out(mod);
}

module *module_new() {
	module *mod = malloc(sizeof(module));

	mod->bpm = 120;
	mod->rpb = 4;
	mod->nseq = 0;
	mod->curr_seq = 0;
	mod->playing = 0;
	mod->recording = 0;
	mod->zero_time = 0;
	mod->song_pos = 0.0;
	mod->mute = 0;
	mod->ctrlpr = DEFAULT_CTRLPR;
	mod->cur_rec_update = 0;
	mod->tline = timeline_new();
	mod->seq = malloc(sizeof(sequence *));
	pthread_mutex_init(&mod->excl, NULL);
	mod->clt = midi_client_new(mod);
	return mod;
}

void module_mute(module *mod) {
	mod->mute = 1;
}

void module_seqs_reindex(module *mod) {
	for (int s = 0; s < mod->nseq; s++) {
		mod->seq[s]->index = s;
	}
}

void module_free(module *mod) {
	midi_stop(mod->clt);
	for (int s = 0; s < mod->nseq; s++)
		sequence_free(mod->seq[s]);

	free(mod->seq);
	timeline_free(mod->tline);
	pthread_mutex_destroy(&mod->excl);
	free(mod);
}

void module_dump_notes(module *mod, int n) {
	mod->clt->dump_notes = n;
}

void module_add_sequence(module *mod, sequence *seq) {
	module_excl_in(mod);

	mod->seq = realloc(mod->seq, sizeof(sequence *) * (mod->nseq + 1));
	mod->seq[mod->nseq++] = seq;
	seq->mod_excl = &mod->excl;
	seq->clt = mod->clt;

	module_seqs_reindex(mod);
	module_excl_out(mod);
}

void module_del_sequence(module *mod, int s) {
	if (s == -1)
		s = mod->nseq - 1;

	if ((s < 0) || (s >= mod->nseq))
		return;

	module_excl_in(mod);

	sequence_free(mod->seq[s]);

	for (int i = s; i < mod->nseq - 1; i++) {
		mod->seq[i] = mod->seq[i + 1];
	}

	mod->nseq--;

	if (mod->nseq == 0) {
		free(mod->seq);
		mod->seq = 0;
	} else {
		mod->seq = realloc(mod->seq, sizeof(sequence *) * mod->nseq);
	}

	module_seqs_reindex(mod);
	module_excl_out(mod);
}

void module_swap_sequence(module *mod, int s1, int s2) {
	if ((s1 < 0) || (s1 >= mod->nseq))
		return;

	if ((s2 < 0) || (s2 >= mod->nseq))
		return;

	if (s1 == s2)
		return;

	module_excl_in(mod);

	sequence *s3 = mod->seq[s1];
	mod->seq[s1] = mod->seq[s2];
	mod->seq[s2] = s3;

	module_seqs_reindex(mod);
	module_excl_out(mod);
}

timeline *module_get_timeline(module *mod) {
	return mod->tline;
}

char *module_get_time(module *mod) {
	static char buff[256];
	sprintf(buff, "%02d:%02d:%03d", mod->min, mod->sec, mod->ms);
	return buff;
}

void module_synch_output_ports(module *mod) {
	midi_buff_excl_in(mod->clt);

	for (int p = 0; p < MIDI_CLIENT_MAX_PORTS; p++) {
		mod->clt->ports_to_open[p] = 0;
		if (mod->clt->curr_midi_queue_event[p])
			mod->clt->ports_to_open[p] = 1;
	}

	mod->clt->ports_to_open[mod->clt->default_midi_port] = 1;

	for (int s = 0; s < mod->nseq; s++)
		for (int t = 0; t < mod->seq[s]->ntrk; t++)
			mod->clt->ports_to_open[mod->seq[s]->trk[t]->port] = 1;

	midi_buff_excl_out(mod->clt);
}
