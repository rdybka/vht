/* sequence.c - Valhalla Tracker (libvht)
 *
 * Copyright (C) 2020 Remigiusz Dybka - remigiusz.dybka@gmail.com
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

#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include "module.h"
#include "sequence.h"
#include "track.h"

void seq_mod_excl_in(sequence *seq) {
	//printf("mod_excl in");
	if (seq->mod_excl)
		pthread_mutex_lock(seq->mod_excl);
	//printf(".\n");
}

void seq_mod_excl_out(sequence *seq) {
	//printf("mod_excl out");
	if (seq->mod_excl)
		pthread_mutex_unlock(seq->mod_excl);
	//printf(".\n");
}

sequence *sequence_new(int length) {
	sequence *seq = malloc(sizeof(sequence));
	seq->ntrk = 0;
	seq->trk = 0;
	seq->pos = 0;
	seq->length = length;
	seq->midi_focus = 0;
	seq->last_period = 0;
	seq->index = 0;
	seq->rpb = 4;

	for (int t = 0; t < 3; t ++) {
		seq->triggers[t].type = seq->triggers[t].channel = seq->triggers[t].note = 0;
	}

	for (int t = 0; t < 3; t++) {
		seq->trg_times[t] = -1;
	}

	seq->trg_times[3] = 0;

	seq->trg_playmode = 0;
	seq->trg_quantise = 1;
	seq->mod_excl = NULL;
	seq->clt = NULL;
	seq->playing = 0;
	seq->lost = 1;
	return seq;
}

void sequence_trk_reindex(sequence *seq) {
	for (int t = 0; t < seq->ntrk; t++) {
		seq->trk[t]->index = t;
	}
}

sequence *sequence_clone(sequence *seq) {
	sequence *ns = sequence_new(seq->length);
	ns->mod_excl = seq->mod_excl;
	ns->clt = seq->clt;
	ns->pos = seq->pos;

	for (int t = 0; t < seq->ntrk; t++) {
		track *trk = track_clone(seq->trk[t]);
		ns->trk = realloc(ns->trk, sizeof(track *) * (ns->ntrk + 1));
		track_wind(trk, seq->pos);
		ns->trk[ns->ntrk++] = trk;
		trk->mod_excl = seq->mod_excl;
		trk->clt = seq->clt;
	}

	sequence_trk_reindex(ns);

	ns->trg_playmode = seq->trg_playmode;
	ns->trg_quantise = seq->trg_quantise;

	for (int t = 0; t < 3; t ++) {
		ns->triggers[t].type = seq->triggers[t].type;
		ns->triggers[t].channel = seq->triggers[t].channel;
		ns->triggers[t].note = seq->triggers[t].note;
	}

	return ns;
}

void sequence_add_track(sequence *seq, track *trk) {
	seq_mod_excl_in(seq);

	seq->trk = realloc(seq->trk, sizeof(track *) * (seq->ntrk + 1));
	seq->trk[seq->ntrk++] = trk;
	trk->mod_excl = seq->mod_excl;
	trk->clt = seq->clt;
	sequence_trk_reindex(seq);
	track_wind(trk, seq->pos);
	seq_mod_excl_out(seq);
	return;
}

track *sequence_clone_track(sequence *seq, track *trk) {
	track *ntrk = track_clone(trk);
	sequence_add_track(seq, ntrk);
	return ntrk;
}

void sequence_double(sequence *seq) {
	if (seq->length > SEQUENCE_MAX_LENGTH / 2)
		return;

	for (int t = 0; t < seq->ntrk; t++)
		track_double(seq->trk[t]);

	seq->length *= 2;
}

void sequence_halve(sequence *seq) {
	if (seq->length < 2)
		return;

	for (int t = 0; t < seq->ntrk; t++)
		track_halve(seq->trk[t]);

	seq->length /= 2;
}

void sequence_free(sequence *seq) {
	for (int t = 0; t < seq->ntrk; t++) {
		track_free(seq->trk[t]);
	}

	if (seq->trk)
		free(seq->trk);

	free(seq);
}

void sequence_advance(sequence *seq, double period, jack_nframes_t nframes) {
	if ((seq->trg_quantise == 0) && (seq->trg_times[2] == -2)) {
		seq->trg_times[2] = -1;
		if (seq->playing && seq->trg_times[3] != -2) {
			seq->playing = 0;
			seq->lost = 1;
			for (int t = 0; t < seq->ntrk; t++)
				track_reset(seq->trk[t]);

		} else {
			seq->playing = 1;
			seq->pos = 0;
			if (seq->trg_playmode == TRIGGER_ONESHOT)
				seq->trg_times[3] = -4;

			for (int t = 0; t < seq->ntrk; t++) {
				track_reset(seq->trk[t]);
			}
		}
	}

	double p = ceil(seq->pos) - seq->pos;
	if (period > p) {
		jack_nframes_t frm = nframes;
		frm *= p / period;

		period -= p;
		nframes -= frm;

		sequence_advance(seq, p, frm);
	}

	if (seq->pos == floor(seq->pos)) {
		int r = (int)seq->pos;
		while (r >= seq->length)
			r-=seq->length;

		//printf("%d %d %d %d\n", seq->trg_times[0], seq->trg_times[1], seq->trg_times[2], seq->trg_times[3]);

		// quantised play
		if (seq->trg_times[2] == r) {
			seq->trg_times[2] = -1;
			if (!seq->playing) {
				seq->playing = 1;
				seq->pos = 0;
				if (seq->trg_playmode == TRIGGER_ONESHOT) {
					seq->trg_times[3] = -2;
					if (r == 0)
						seq->trg_times[3]--;
				}

				for (int t = 0; t < seq->ntrk; t++)
					track_reset(seq->trk[t]);
			} else {
				seq->playing = 0;
				seq->lost = 1;
				for (int t = 0; t < seq->ntrk; t++)
					track_reset(seq->trk[t]);
			}
		}

		if (seq->trg_playmode == TRIGGER_HOLD && seq->trg_times[3] == -23 && seq->playing) {
			// let it go, let it go
			seq->trg_times[3] = 0;
			seq->playing = 0;
			seq->lost = 1;
			for (int t = 0; t < seq->ntrk; t++)
				track_reset(seq->trk[t]);
		}

		if(r == 0 && seq->trg_playmode == TRIGGER_ONESHOT && seq->playing) {
			if (seq->trg_times[3] < 0) {
				seq->trg_times[3]++;
			}

			if ((seq->trg_times[3] == -1) && (seq->trg_times[2] == -1)) {
				seq->trg_times[3] = 0;
				seq->playing = 0;
				seq->lost = 1;
				for (int t = 0; t < seq->ntrk; t++)
					track_reset(seq->trk[t]);
			}
		}

		// cue trigger
		if (r == 0) {
			if (seq->trg_times[1] > -1) {
				seq->trg_times[1] = -1;

				if (seq->playing) {
					seq->playing = 0;
					for (int t = 0; t < seq->ntrk; t++)
						track_reset(seq->trk[t]);
				} else {
					seq->playing = 1;
					for (int t = 0; t < seq->ntrk; t++)
						track_reset(seq->trk[t]);
				}
			}
		}
	}

	int resync = 0;
	// mute trigger
	if (seq->trg_times[0] > -1) {
		seq->trg_times[0] = -1;

		if(seq->playing) {
			seq->playing = 0;
			for (int t = 0; t < seq->ntrk; t++) {
				track_kill_notes(seq->trk[t]);
			}
		} else {
			seq->playing = 1;
			resync = 1;
		}
	}

	if (resync) {
		for (int t = 0; t < seq->ntrk; t++) {
			seq->trk[t]->resync = 0;
			seq->trk[t]->pos = 0;
			track_wind(seq->trk[t], seq->pos);
			track_advance(seq->trk[t], period, nframes);
		}
	}

	seq->last_period = period;
	if (seq->playing) {
		// resync tracks
		for (int t = 0; t < seq->ntrk; t++) {
			if (seq->trk[t]->resync) {
				seq->trk[t]->resync = 0;
				seq->trk[t]->pos = 0;
				track_wind(seq->trk[t], seq->pos);
				track_advance(seq->trk[t], period, nframes);
			}
		}

		for (int t = 0; t < seq->ntrk; t++) {
			track_advance(seq->trk[t], period, nframes);

			// if track past end, stop playing
			if (seq->trk[t]->pos > seq->trk[t]->nrows)

				if (!seq->trk[t]->loop)
					seq->trk[t]->playing = 0;
		}
	}

	seq->pos += period;

	if (seq->pos > seq->length)
		seq->pos -= seq->length;
}

void sequence_del_track(sequence *seq, int t) {
	if (t == -1)
		t = seq->ntrk - 1;

	if ((t >= seq->ntrk) || (t < 0))
		return;

	seq->trk[t]->kill = 1;
	if (seq->playing && seq->trk[t]->playing && seq->trk[t]->clt)
		while(seq->trk[t]->kill);

	seq_mod_excl_in(seq);

	track_free(seq->trk[t]);

	for (int i = t; i < seq->ntrk - 1; i++) {
		seq->trk[i] = seq->trk[i + 1];
	}

	seq->ntrk--;

	if (seq->ntrk  == 0) {
		free(seq->trk);
		seq->trk = 0;
	} else {
		seq->trk = realloc(seq->trk, sizeof(track *) * seq->ntrk);
	}

	sequence_trk_reindex(seq);
	seq_mod_excl_out(seq);
}

void sequence_swap_track(sequence *seq, int t1, int t2) {
	if ((t1 < 0) || (t1 >= seq->ntrk))
		return;

	if ((t2 < 0) || (t2 >= seq->ntrk))
		return;

	if (t1 == t2)
		return;

	seq_mod_excl_in(seq);

	track *t3 = seq->trk[t1];
	seq->trk[t1] = seq->trk[t2];
	seq->trk[t2] = t3;
	sequence_trk_reindex(seq);
	seq_mod_excl_out(seq);
}

void sequence_set_midi_focus(sequence *seq, int foc) {
	seq->midi_focus = foc;
}

void sequence_set_length(sequence *seq, int length) {
	seq_mod_excl_in(seq);
	for (int t = 0; t < seq->ntrk; t++) {
		if((seq->trk[t]->nrows == seq->trk[t]->nsrows) && (seq->trk[t]->nrows == seq->length)) {
			track_resize(seq->trk[t], length);
			seq->trk[t]->nsrows = length;
		}
	}

	seq->length = length;
	seq->lost = 1;
	seq_mod_excl_out(seq);
}

int sequence_get_playing(sequence *seq) {
	return seq->playing;
}

int sequence_get_cue(sequence *seq) {
	if (seq->trg_times[1] == -1) {
		return 0;
	} else {
		return 1;
	}
}

void sequence_set_playing(sequence *seq, int p) {
	if (!p) {
		seq->playing = 0;
	} else {
		seq->playing = 1;
	}
}

void sequence_handle_record(module *mod, sequence *seq, midi_event evt) {
	if (!seq->playing)
		return;

	if (mod->recording == 1)
		if (seq->midi_focus >= 0 && seq->midi_focus < seq->ntrk) {
			track_handle_record(seq->trk[seq->midi_focus], evt);
			evt.channel = seq->trk[seq->midi_focus]->channel;
			midi_buffer_add(mod->clt, seq->trk[seq->midi_focus]->port, evt);
		}

	if (mod->recording == 2) {
		midi_buffer_add(mod->clt, mod->clt->default_midi_port, evt);
		int found = 0;
		for (int tr = seq->ntrk - 1; tr > -1 && !found; tr--) {
			if ((seq->trk[tr]->channel == evt.channel) && (seq->trk[tr]->port == mod->clt->default_midi_port)) {
				track_handle_record(seq->trk[tr], evt);
				found = 1;
			}
		}

		if (!found) {
			track *trk;
			trk = track_new(mod->clt->default_midi_port, evt.channel, seq->length, seq->length, mod->ctrlpr);

			// sequence_add_track(seq, trk); can't call it from here because of mutex - copy code, bad design
			seq->trk = realloc(seq->trk, sizeof(track *) * (seq->ntrk + 1));
			seq->trk[seq->ntrk++] = trk;
			trk->mod_excl = seq->mod_excl;
			trk->clt = seq->clt;
			sequence_trk_reindex(seq);

			trk->last_pos = seq->pos - seq->last_period;
			trk->pos = seq->pos;
			trk->last_period = seq->last_period;

			if (trk->last_pos < 0) {
				trk->last_pos += seq->length;
			}

			track_handle_record(trk, evt);
			trk->pos = seq->pos;
		}
	}
}

void sequence_trigger_mute(sequence *seq) {
	//printf("mute %d\n", seq->index);
	seq->trg_times[0] = 0;
}


void sequence_trigger_cue(sequence *seq) {
	//printf("cue %d\n", seq->index);
	if (seq->trg_times[1] == -1) {
		seq->trg_times[1] = 0;
	} else {
		seq->trg_times[1] = -1;
	}
}

void sequence_trigger_play_on(sequence *seq) {
	//printf("play %d\n", seq->index);

	if ((seq->trg_playmode == TRIGGER_HOLD) && (seq->playing)) {
		seq->trg_times[3] = 0;
		return;
	}

	if (seq->playing) {
		int np = ceil(seq->pos);

		while(np >= seq->length)
			np-=seq->length;

		seq->trg_times[2] = np;
		return;
	}

	if (seq->trg_quantise == 0) {
		seq->trg_times[2] = -2;
	} else {
		int np = ceil(seq->pos);

		while(np++ % seq->trg_quantise);
		np--; //:)

		while(np >= seq->length)
			np-=seq->length;

		seq->trg_times[2] = np;
	}
}

void sequence_trigger_play_off(sequence *seq) {
	//printf("release %d : %d\n", seq->index, seq->playing);

	if (seq->trg_playmode == TRIGGER_HOLD) {
		if (seq->playing) {
			seq->trg_times[3] = -23;
		}  else {
			seq->playing = 0;
			seq->lost = 1;
			seq->trg_times[3] = 0;
			seq->trg_times[2] = -1;
			for (int t = 0; t < seq->ntrk; t++)
				track_reset(seq->trk[t]);

		}
	}
}
