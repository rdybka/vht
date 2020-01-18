/* sequence.c - Valhalla Tracker (libvht)
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

#include <stdlib.h>
#include <stdio.h>
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

	for (int t = 0; t < 3; t ++) {
		seq->triggers[t].type = seq->triggers[t].channel = seq->triggers[t].note = 0;
	}

	seq->trg_playmode = 0;
	seq->trg_quantise = 1;
	seq->mod_excl = NULL;
	seq->clt = NULL;
	return seq;
}

void sequence_trk_reindex(sequence *seq) {
	for (int t = 0; t < seq->ntrk; t++) {
		seq->trk[t]->index = t;
	}
}

void sequence_add_track(sequence *seq, track *trk) {
	seq_mod_excl_in(seq);

	seq->trk = realloc(seq->trk, sizeof(track *) * (seq->ntrk + 1));
	track_wind(trk, seq->pos);
	seq->trk[seq->ntrk++] = trk;
	trk->mod_excl = seq->mod_excl;
	trk->clt = seq->clt;
	sequence_trk_reindex(seq);
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

void sequence_advance(sequence *seq, double period) {
	seq->last_period = period;
	for (int t = 0; t < seq->ntrk; t++) {
		track_advance(seq->trk[t], period);

		// if track past end, stop playing
		if (seq->trk[t]->pos > seq->trk[t]->nrows)
			if (!seq->trk[t]->loop)
				seq->trk[t]->playing = 0;
	}

	// resync tracks
	for (int t = 0; t < seq->ntrk; t++) {
		if (seq->trk[t]->resync) {
			seq->trk[t]->resync = 0;
			seq->trk[t]->pos = 0;
			track_wind(seq->trk[t], seq->pos);
			track_advance(seq->trk[t], period);
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
	seq_mod_excl_out(seq);
}

void sequence_handle_record(module *mod, sequence *seq, midi_event evt) {
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
