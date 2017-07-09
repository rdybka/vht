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

#include "sequence.h"
 
sequence *sequence_new() {
	sequence *seq = malloc(sizeof(sequence));
	seq->ntrk = 0;
	seq->trk = 0;
	return seq;
}

void sequence_add_track(sequence *seq, track *trk) {
	// fresh?
	if (seq->ntrk == 0) {
		seq->trk = malloc(sizeof(track *));
		seq->trk[0] = trk;
		seq->ntrk = 1;
		return;
	}
}

void sequence_free(sequence *seq) {
	for (int t = 0; t < seq->ntrk; t++) {
		track_free(seq->trk[t]);
	}
	
	if (seq->trk)
		free(seq->trk);
	
	free(seq);
}
