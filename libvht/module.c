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
#include "track.h"
#include "module.h"
#include "midi_event.h"
#include "jack_process.h"
#include "jack_client.h"

struct module_t module;
struct rec_update_t rec_update[EVT_BUFFER_LENGTH];
int cur_rec_update;

int lastsec;

void module_excl_in() {
	if (!module.jack_running)
		return;

	pthread_mutex_lock(&module.excl);
}

void module_excl_out() {
	if (!module.jack_running)
		return;

	pthread_mutex_unlock(&module.excl);
}

// the GOD function
void module_advance(jack_nframes_t curr_frames) {
	if (module.nseq == 0)
		return;

	module_excl_in();

	midi_buffer_clear();

	if (!module.playing) {
		// are we paused?
		if (module.zero_time > 0)
			module.zero_time += jack_buffer_size;
	}

	// are we muting after stop?
	if (!module.playing && module.mute) {
		for (int t = 0; t < module.seq[module.curr_seq]->ntrk; t++)
			track_kill_notes(module.seq[module.curr_seq]->trk[t]);

		module.mute = 0;
	}

	if (module.zero_time == 0)
		module.zero_time = curr_frames;

	double time = (curr_frames - module.zero_time) / (double)jack_sample_rate;
	double row_length = 60.0 / ((double)module.rpb * (double)module.bpm);
	double period = ((double)jack_buffer_size / (double)jack_sample_rate) / row_length;

	module.sec = time;
	module.min = module.sec / 60;
	module.sec -= (module.min * 60);

	module.ms = (time - floorf(time)) * 1000;

	if (module.playing)
		timeline_advance(module.tline, period);

// handle input from MIDI
	void *inp = jack_port_get_buffer(jack_input_port, jack_buffer_size);

	jack_nframes_t ninp;
	jack_midi_event_t evt;

	ninp = jack_midi_get_event_count(inp);

	int empty = 0;

	for (jack_nframes_t n = 0; (n < ninp) && !empty; n++) {
		empty = jack_midi_event_get(&evt, inp, n);
		if (!empty) {
			midi_event mev = midi_decode_event(evt.buffer, evt.size);
			mev.time = evt.time;

			if (!module.recording) {
				midi_buffer_add(default_midi_port, mev);
			}

			midi_in_buffer_add(mev);

			int ignore = 0;

			midi_ignore_buff_excl_in();
			for (int f = 0; f < curr_midi_ignore_event; f++) {
				midi_event ignev = midi_ignore_buffer[f];
				if (ignev.channel == mev.channel)
					if (ignev.type == mev.type)
						if (ignev.note == mev.note)
							ignore = 1;
			}

			midi_ignore_buff_excl_out();

			if (module.recording && !ignore) {
				sequence_handle_record(module.seq[module.curr_seq], mev);
			}
		}
	}

	//printf("time: %02d:%02d:%03d %3.5f %d\n", module.min, module.sec, module.ms, period, module.bpm);
	module.song_pos += period;
	module_excl_out();
}

void module_new() {
	module_excl_in();
	module_free();
	module.bpm = 120;
	module.def_nrows = 64;
	module.rpb = 4;
	module.seq = NULL;
	module.nseq = 0;
	module.curr_seq = 0;
	module.playing = 0;
	module.recording = 0;
	module.zero_time = 0;
	module.song_pos = 0.0;
	module.mute = 0;
	module.dump_notes = 0;
	module.ctrlpr = DEFAULT_CTRLPR;
	cur_rec_update = 0;
	module.tline = timeline_new();

	module_excl_out();
}

void module_mute() {
	module.mute = 1;
}

void module_seqs_reindex() {
	for (int s = 0; s < module.nseq; s++) {
		module.seq[s]->index = s;
	}
}

void module_free() {
	// fresh start?
	if (module.bpm == -1) {
		return;
	}

	if (module.seq != NULL) {
		for (int s = 0; s < module.nseq; s++)
			sequence_free(module.seq[s]);

		free(module.seq);
		module.seq = NULL;
		module.bpm = -1;
	}

	if (module.tline != NULL) {
		timeline_free(module.tline);
		module.tline = NULL;
	}
}

void module_dump_notes(int n) {
	module.dump_notes = n;
}

void module_add_sequence(sequence *seq) {
	module_excl_in();

	// fresh module
	if (module.nseq == 0) {
		module.seq = malloc(sizeof(sequence *));
		module.seq[0] = seq;
		module.nseq = 1;
		module_seqs_reindex();
		module_excl_out();
		return;
	}

	module.seq = realloc(module.seq, sizeof(sequence *) * (module.nseq + 1));
	module.seq[module.nseq++] = seq;

	module_seqs_reindex();
	module_excl_out();
}

void module_del_sequence(int s) {
	if (s == -1)
		s = module.nseq - 1;

	if ((s < 0) || (s >= module.nseq))
		return;

	module_excl_in();

	sequence_free(module.seq[s]);

	for (int i = s; i < module.nseq - 1; i++) {
		module.seq[i] = module.seq[i + 1];
	}

	module.nseq--;

	if (module.nseq == 0) {
		free(module.seq);
		module.seq = 0;
	} else {
		module.seq = realloc(module.seq, sizeof(sequence *) * module.nseq);
	}

	module_seqs_reindex();
	module_excl_out();
}

void module_swap_sequence(int s1, int s2) {
	if ((s1 < 0) || (s1 >= module.nseq))
		return;

	if ((s2 < 0) || (s2 >= module.nseq))
		return;

	if (s1 == s2)
		return;

	module_excl_in();

	sequence *s3 = module.seq[s1];
	module.seq[s1] = module.seq[s2];
	module.seq[s2] = s3;

	module_seqs_reindex();
	module_excl_out();
}

timeline *module_get_timeline(void) {
	return module.tline;
}

char *module_get_time(void) {
	static char buff[256];
	sprintf(buff, "%02d:%02d:%03d", module.min, module.sec, module.ms);
	return buff;
}
