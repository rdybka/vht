/* sequence.c
 *
 * Copyright (C) 2017 Remigiusz Dybka
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

sequence *sequence_new(int length) {
	sequence *seq = malloc(sizeof(sequence));
	seq->ntrk = 0;
	seq->trk = 0;
	seq->pos = 0;
	seq->length = length;
	seq->midi_focus = 0;
	seq->last_period = 0;
	return seq;
}

void sequence_add_track(sequence *seq, track *trk) {
	module_excl_in();
	// fresh?
	if (seq->ntrk == 0) {
		seq->trk = malloc(sizeof(track *));
	}

	seq->trk = realloc(seq->trk, sizeof(track *) * (seq->ntrk + 1));
	track_wind(trk, seq->pos);
	seq->trk[seq->ntrk++] = trk;
	module_excl_out();
	return;
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
		//if (seq->trk[t]->playing) {
		track_advance(seq->trk[t], period);

		// if track past end, stop playing
		if (seq->trk[t]->pos > seq->trk[t]->nrows)
			if (!seq->trk[t]->loop)
				seq->trk[t]->playing = 0;
		//}
	}

	// will we reach the end of sequence?
	// if so, reset non-looping tracks
	if (seq->pos + period > seq->length) {
		// reset track positions
		for (int t = 0; t < seq->ntrk; t++) {
			if (!seq->trk[t]->loop) {
				seq->trk[t]->pos = 0;
				track_wind(seq->trk[t], (double)seq->length - (seq->pos + period));
				track_advance(seq->trk[t], period);
			}
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

	module_excl_in();

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

	module_excl_out();
}

void sequence_swap_track(sequence *seq, int t1, int t2) {
	if ((t1 < 0) || (t1 >= seq->ntrk))
		return;

	if ((t2 < 0) || (t2 >= seq->ntrk))
		return;

	if (t1 == t2)
		return;

	module_excl_in();

	track *t3 = seq->trk[t1];
	seq->trk[t1] = seq->trk[t2];
	seq->trk[t2] = t3;

	module_excl_out();
}

void sequence_set_midi_focus(sequence *seq, int foc) {
	seq->midi_focus = foc;
}

void sequence_handle_record(sequence *seq, midi_event evt) {
	if (module.recording == 1)
		if (seq->midi_focus >= 0 && seq->midi_focus < seq->ntrk)
			track_handle_record(seq->trk[seq->midi_focus], evt);

	if (module.recording == 2) {
		int found = 0;
		for (int tr = 0; tr < seq->ntrk; tr++) {
			if (seq->trk[tr]->channel == evt.channel) {
				track_handle_record(seq->trk[tr], evt);
				found = 1;
			}
		}

		if (!found) {
			track *trk;
			trk = track_new(0, evt.channel, seq->length, seq->length);
			trk->last_pos = seq->pos - seq->last_period;
			trk->pos = seq->pos;
			trk->last_period = seq->last_period;

			if (trk->last_pos < 0) {
				trk->last_pos += seq->length;
			}

			sequence_add_track(seq, trk);
			track_handle_record(trk, evt);
			trk->pos = seq->pos;
		}
	}
}
