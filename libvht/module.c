/* module.c - vahatraker (libvht)
 *
 * Copyright (C) 2024 Remigiusz Dybka - remigiusz.dybka@gmail.com
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

#include <unistd.h>
#include <stdio.h>
#include <math.h>
#include <pthread.h>
#include "module.h"
#include "midi_client.h"
#include "track.h"
#include "midi_event.h"
#include "smf.h"

struct rec_update_t rec_update[MIDI_EVT_BUFFER_LENGTH];
int cur_rec_update;

int lastsec;

void module_excl_in(module *mod) {
	pthread_mutex_lock(&mod->excl);
}

void module_excl_out(module *mod) {
	pthread_mutex_unlock(&mod->excl);
}

void mod_should_save(module *mod) {
	mod->should_save = 1;
}

void module_handle_inception(track *trk, midi_event evt) {
	midi_client *clt = (midi_client *)trk->clt;
	module *mod = (module *)clt->mod_ref;

	if (mod->inception && trk->port == 15) {
		for (int s = 0; s < mod->nseq; s++)
			sequence_handle_trigger_event(mod->seq[s], evt);
	}
}

// the god-function
void module_advance(module *mod, jack_nframes_t curr_frames) {
	if (mod->panic) {
		for (int s = 0; s < mod->nseq; s++)
			mod->seq[s]->thumb_panic = 2;

		for (int s = 0; s < mod->tline->nstrips; s++) {
			mod->tline->strips[s].seq->thumb_panic = 2;
		}
	}

	if (mod->playing < 0) {
		mod->playing++;
		if (mod->playing == 0) {
			mod->playing = 1;
			mod->zero_time = curr_frames;
		} else {
			return;
		}
	}

	if (mod->nseq == 0) {
		return;
	}

	if (mod->render_mode == 23 && !mod->playing) {
		return;
	}

	if (mod->render_mode == 23 && mod->playing) {
		double t = (curr_frames - mod->end_time) / (double)mod->clt->jack_sample_rate;
		if (t > mod->render_lead_out) {
			mod->playing = 0;
			return;
		}
	}

	module_excl_in(mod);

	double time = (curr_frames - mod->zero_time) / (double)mod->clt->jack_sample_rate;
	if (mod->zero_time == 0)
		time = 0;
	//double row_length = 60.0 / (double)mod->bpm;
	double period = ((double)mod->clt->jack_buffer_size / (double)mod->clt->jack_sample_rate);

	// are we muting after stop?
	if (!mod->playing) {
		if (mod->mute) {
			for (int s = 0; s < mod->nseq; s++)
				for (int t = 0; t < mod->seq[s]->ntrk; t++)
					track_kill_notes(mod->seq[s]->trk[t]);

			for (int s = 0; s < mod->tline->nstrips; s++) {
				timestrip *strp = &mod->tline->strips[s];
				for (int t = 0; t < strp->seq->ntrk; t++) {
					track_kill_notes(strp->seq->trk[t]);
				}
			}
			mod->mute = 0;
		}
		if (mod->zero_time)
			mod->zero_time += curr_frames - mod->clt->jack_last_frame;
	} else {
		mod->sec = time;
		mod->min = mod->sec / 60;
		mod->sec -= (mod->min * 60);

		mod->ms = (time - floorf(time)) * 1000;
	}

	if ((mod->playing) && (mod->zero_time == 0)) {
		mod->zero_time = curr_frames;
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

			// handle triggers
			for (int s = 0; s < mod->nseq; s++)
				sequence_handle_trigger_event(mod->seq[s], mev);

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

			if (mod->recording && !ignore) {
				sequence_handle_record(mod, mod->curr_seq, mev);
			}

			if (mod->curr_seq) {
				for (int t = 0; t < mod->curr_seq->ntrk; t++) {
					if (mod->curr_seq->trk[t]->channel == mev.channel) {
						mod->curr_seq->trk[t]->indicators |= 1;
					}
				}
			}
			midi_ignore_buff_excl_out(mod->clt);
		}
	}

	if (mod->playing) {
		if (mod->play_mode == 0) {
			for (int s = 0; s < mod->nseq; s++) {
				sequence *seq = mod->seq[s];
				if (seq->lost) {
					seq->pos = fmod(mod->song_pos * seq->rpb * (mod->bpm / 60.0), seq->length);

					for (int t = 0; t < seq->ntrk; t++) {
						seq->trk[t]->pos = seq->pos;
					}
					seq->lost = 0;
				}

				double pp = period * seq->rpb * (mod->bpm / 60.0);
				int frm = mod->clt->jack_buffer_size;
				if (mod->render_mode == 1) // don't overfeed while exporting
					if (seq->pos + pp > seq->length) {
						double ppp = seq->length - seq->pos;
						frm = frm * (ppp / pp);
						pp = ppp;
					}

				sequence_advance(seq, pp, frm);
			}
		}

		if (mod->play_mode == 1) {
			double per = period;

			if (mod->switch_req && mod->switch_delay < period) {
				per = mod->switch_delay;
			}

			timeline_advance(mod->tline, per, mod->clt->jack_buffer_size);
		}

		for (int s = 0; s < mod->nseq; s++) {
			sequence_handle_triggers_post_adv(mod->seq[s], period * mod->seq[s]->rpb * (mod->bpm / 60.0), mod->clt->jack_buffer_size);
		}

		if (mod->midi_file)
			smf_set_pos(mod->midi_file, curr_frames);

		mod->song_pos += period;

		// fix mode switching
		if (mod->switch_req && mod->nseq) {
			//printf("delaying: %f\n", mod->switch_delay);

			if (mod->play_mode == 0) {
				double per = period * mod->seq[0]->rpb * (mod->bpm / 60.0);
				mod->switch_delay -= per;


				if (mod->switch_delay < 0.00000001) {
					if (fabs(mod->switch_delay) < 0.0000001) { // round off
						mod->switch_delay = 0.0;
					}

					int frm = (double)mod->clt->jack_buffer_size * (fabs(mod->switch_delay) / per);

					if (frm) {
						timeline_advance(mod->tline, -mod->switch_delay, frm);
					}

					mod->switch_delay = 0;
					mod->switch_req = 0;
					mod->play_mode = 1;
				}
			}
		}
	} else {
		// send program changes paused
		for (int s = 0; s < mod->nseq; s++) {
			for (int t = 0; t < mod->seq[s]->ntrk; t++)
				track_fix_program_change(mod->seq[s]->trk[t]);
		}
	}

	//printf("%f %f %f %d %d\n", mod->song_pos, mod->seq[0]->pos, timeline_get_qb_time(mod->tline, mod->tline->pos), mod->clt->jack_buffer_size, mod->clt->jack_sample_rate);
	module_excl_out(mod);
}

void module_set_render_mode(module *mod, int mode) {
	mod->render_mode = mode;
	//if (mode == 0)
	//midi_set_freewheel(mod->clt, 0);
}

int module_get_render_mode(module *mod) {
	return mod->render_mode;
}

void module_set_pnq_hack(module *mod, int ph) {
	mod->pnq_hack = ph;
}

int module_get_pnq_hack(module *mod) {
	return mod->pnq_hack;
}

void module_set_inception(module *mod, int i) {
	mod->inception = i;
}

int module_get_inception(module *mod) {
	return mod->inception;
}

void module_set_should_save(module *mod, int ss) {
	mod->should_save = ss;
}

int module_get_should_save(module *mod) {
	return mod->should_save;
}

void module_play(module *mod, int play) {
	module_excl_in(mod);
	int prev_state = mod->playing;

	mod->playing = play;

	if (mod->render_mode > 0 && mod->playing && !prev_state) {
		mod->playing = -2; // this will skip first callback from jack
		midi_set_freewheel(mod->clt, 1);
	}

	module_excl_out(mod);

	if (play == 0) {
		module_mute(mod);
	}

	if (mod->transp && !mod->render_mode) {
		midi_send_transp(mod->clt, play, -1);
	}
}

module *module_new() {
	module *mod = malloc(sizeof(module));

	mod->bpm = 120;
	mod->nseq = 0;
	mod->curr_seq = 0;
	mod->playing = 0;
	mod->recording = 0;
	mod->zero_time = 0;
	mod->song_pos = 0.0;
	mod->mute = 0;
	mod->ctrlpr = DEFAULT_CTRLPR;
	mod->cur_rec_update = 0;
	mod->seq = malloc(sizeof(sequence *));
	mod->transp = 0;
	pthread_mutex_init(&mod->excl, NULL);
	mod->clt = midi_client_new(mod);
	mod->midi_file = smf_new(mod);
	mod->tline = timeline_new(mod->clt);
	mod->play_mode = 0;
	mod->switch_delay = 0.0;
	mod->switch_req = 0;
	mod->render_mode = 0;
	mod->render_lead_out = 0;
	mod->panic = 0;
	timechange *tc = timeline_get_change(mod->tline, 0);
	tc->bpm = mod->bpm;
	tc->row = 0;
	tc->linked = 0;
	mod->pnq_hack = 0;
	mod->inception = 0;
	mod->should_save = 0;
	timeline_update(mod->tline);

	return mod;
}

void module_mute(module *mod) {
	mod->mute = 1;
}

int module_dump_midi(module *mod, const char *phname, int tc, int tpf) {
	mod->midi_file->tc = tc;
	mod->midi_file->ticks = tpf;
	return smf_dump(mod->midi_file, phname);
}

void module_reset(module *mod) {
	mod->zero_time = 0;
	mod->song_pos = 0;
	mod->min = mod->sec = mod->ms = 0;

	for (int s = 0; s < mod->nseq; s++) {
		mod->seq[s]->pos = 0;
		for (int t = 0; t < mod->seq[s]->ntrk; t++) {
			track_kill_notes(mod->seq[s]->trk[t]);
		}
	}

	midi_buff_excl_in(mod->clt);
	midi_buffer_clear(mod->clt);
	smf_clear(mod->midi_file);
	smf_set_pos(mod->midi_file, 0);
	midi_buff_excl_out(mod->clt);

	for (int s = 0; s < mod->nseq; s++) {
		mod->seq[s]->pos = 0;
		for (int t = 0; t < mod->seq[s]->ntrk; t++) {
			track_reset(mod->seq[s]->trk[t]);
		}
	}

	timeline_reset(mod->tline);
	if (mod->transp)
		midi_send_transp(mod->clt, mod->playing, 0);
}

void module_panic(module *mod, int brutal) {
	for (int s = 0; s < mod->nseq; s++) {
		for (int t = 0; t < mod->seq[s]->ntrk; t++) {
			track_kill_notes(mod->seq[s]->trk[t]);
			if (brutal)
				queue_midi_ctrl(mod->clt, mod->seq[s], mod->seq[s]->trk[t], 0, 0x7B);
		}

		mod->seq[s]->thumb_panic = 9;
	}

	for (int s = 0; s < mod->tline->nstrips; s++) {
		for (int t = 0; t < mod->tline->strips[s].seq->ntrk; t++) {
			track_kill_notes(mod->tline->strips[s].seq->trk[t]);
		}

		mod->tline->strips[s].seq->thumb_panic = 9;
	}

	mod->panic = 1;
}

void module_unpanic(module *mod) {
	mod->panic = 0;
}

void module_seqs_reindex(module *mod) {
	for (int s = 0; s < mod->nseq; s++) {
		mod->seq[s]->index = s;
	}
}

void module_free(module *mod) {
	for (int s = 0; s < mod->nseq; s++)
		for (int t = 0; t < mod->seq[s]->ntrk; t++)
			track_kill_notes(mod->seq[s]->trk[t]);

	smf_free(mod->midi_file);

	sleep(.420);

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

	if (!mod->play_mode) {
		if (mod->nseq > 1) {
			seq->pos = mod->seq[0]->pos;
			seq->lost = 0;
		}
		//seq->pos = mod->song_pos;
	} else {
		if (mod->nseq) {
			seq->pos = mod->seq[0]->pos;
		}
	}

	for (int t = 0; t < seq->ntrk; t++) {
		seq->trk[t]->clt = mod->clt;

		if (seq->pos > 0.0) {
			track_wind(seq->trk[t], seq->pos);
		}
	}

	module_seqs_reindex(mod);
	module_excl_out(mod);
	mod_should_save(mod);
}

void module_del_sequence(module *mod, int s) {
	if (s == -1)
		s = mod->nseq - 1;

	if ((s < 0) || (s >= mod->nseq))
		return;

	module_excl_in(mod);

	timeline_delete_all_strips(mod->tline, s);

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
	mod_should_save(mod);
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

	timeline_swap_sequence(mod->tline, s1, s2);
	module_excl_out(mod);
	mod_should_save(mod);
}

sequence *module_sequence_replace(module *mod, int s, sequence *seq) {
	if (s < 0 || s >= mod->nseq)
		return NULL;

	module_excl_in(mod);
	sequence_set_extras(seq, mod->seq[s]->extras);

	sequence_free(mod->seq[s]);
	mod->seq[s] = seq;
	module_seqs_reindex(mod);

	seq->pos = mod->song_pos;

	for (int t = 0; t < seq->ntrk; t++) {
		seq->trk[t]->clt = mod->clt;

		if (seq->pos > 0.0) {
			track_wind(seq->trk[t], seq->pos);
		}
	}

	module_excl_out(mod);
	mod_should_save(mod);
	return seq;
}

timeline *module_get_timeline(module *mod) {
	return mod->tline;
}

char *module_get_time(module *mod) {
	static char buff[256];
	sprintf(buff, "%02d:%02d:%03d", mod->min, mod->sec, mod->ms);
	return buff;
}


sequence *module_get_curr_seq(module *mod) {
	return mod->curr_seq;
}

void module_set_curr_seq(module *mod, int t, int s) {
	//printf("curr seq: %d:%d\n", t, s);
	if (t > -1) {
		mod->curr_seq = mod->tline->strips[s].seq;
	} else {
		mod->curr_seq = mod->seq[s];
	}
}

double module_get_jack_pos(module *mod) {
	double row_length = 60.0 / ((double)mod->bpm);
	return (mod->song_pos + (((jack_frame_time(mod->clt->jack_client) - mod->clt->jack_last_frame) / (double)mod->clt->jack_sample_rate) / row_length));
}

void module_synch_output_ports(module *mod) {
	midi_buff_excl_in(mod->clt);

	for (int p = 0; p < MIDI_CLIENT_MAX_PORTS; p++) {
		mod->clt->autoports[p] = 0;
		if (mod->clt->curr_midi_queue_event[p])
			mod->clt->autoports[p] = 1;
	}

	for (int s = 0; s < mod->nseq; s++)
		for (int t = 0; t < mod->seq[s]->ntrk; t++)
			mod->clt->autoports[mod->seq[s]->trk[t]->port] = 1;

	midi_buff_excl_out(mod->clt);
}

void module_set_play_mode(module *mod, int m) {
	module_excl_in(mod);

	if (mod->playing) {
		if (mod->play_mode == 0) {
			if (mod->tline->pos == 0.0) {
				mod->switch_delay = mod->seq[0]->length - mod->seq[0]->pos;
				mod->switch_req = 1;
			}

			int imm = 1;

			for (int s = 0; s < mod->nseq; s++) {
				if (mod->seq[s]->playing)
					imm = 0;
			}

			if (imm) {
				// if no seqs play
				mod->play_mode = 1;
				timeline_set_pos(mod->tline, mod->tline->pos, 0);
				mod->switch_req = 1;
				mod->switch_delay = 0;

			} else {
				if (mod->tline->pos > 0.0) {
					double rl = sequence_get_relative_length(mod->seq[0]);
					double rat = mod->seq[0]->length / rl;
					mod->switch_delay = (fmod(mod->tline->pos, rl) * rat) + mod->seq[0]->length - (mod->seq[0]->pos);
					mod->switch_req = 1;
				}
			}
		}

		if (mod->play_mode == 1) {
			for (int s = 0; s < mod->nseq; s++) {
				mod->seq[s]->lost = 0;
			}
			mod->play_mode = 0;
		}
	} else {
		if (!m) {
			mod->play_mode = 0;
		} else {
			mod->play_mode = 1;
		}
	}

	module_excl_out(mod);
}

int module_get_play_mode(module *mod) {
	return mod->play_mode;
}

void module_set_transport(module *mod, int t) {
	if (t) {
		mod->transp = 1;
	} else {
		mod->transp = 0;
	}
}
int module_get_transport(module *mod) {
	return mod->transp;
}

void module_synch_transp(module *mod, int play, jack_nframes_t frames) {
	if (!mod->transp)
		return;

	double pos = (double)frames / mod->clt->jack_sample_rate;
	module_excl_in(mod);

	if (play) {
		mod->playing = 1;
	} else {
		mod->playing = 0;
	}

	while(pos > mod->tline->time_length)
		pos -= mod->tline->time_length;

	double rpos = timeline_get_qb(mod->tline, pos);
	double rem = pos - mod->tline->slices[(long)rpos].time;
	rpos += rem / mod->tline->slices[(long)rpos].length;

	if (rpos >= mod->tline->length)
		rpos = 0;

	mod->transp = 0;
	timeline_set_pos(mod->tline, rpos, 0);
	mod->transp = 1;

	module_excl_out(mod);
}

void module_set_freewheel(module *mod, int on) {
	midi_set_freewheel(mod->clt, on);
}
