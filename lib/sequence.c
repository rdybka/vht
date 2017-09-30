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

#include "sequence.h"

sequence *sequence_new() {
    sequence *seq = malloc(sizeof(sequence));
    seq->ntrk = 0;
    seq->trk = 0;
    seq->pos = 0;
    seq->length = 16;
    return seq;
}

void sequence_add_track(sequence *seq, track *trk) {
    // fresh?
    if (seq->ntrk == 0) {
        seq->trk = malloc(sizeof(track *));
    }

    seq->trk[seq->ntrk++] = trk;
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
    for (int t = 0; t < seq->ntrk; t++) {
        if (seq->trk[t]->playing) {
            track_advance(seq->trk[t], period);

            // if track past end, stop playing
            if (seq->trk[t]->pos > seq->trk[t]->nrows)
                if (!seq->trk[t]->loop)
                    seq->trk[t]->playing = 0;
        }
    }

    // will we reach the end of sequence?
    // if so, reset non-looping tracks
    if (seq->pos + period > seq->length) {
        // reset track positions
        for (int t = 0; t < seq->ntrk; t++) {
            if (!seq->trk[t]->loop) {
                seq->trk[t]->pos = 0;
                seq->trk[t]->playing = 1;
                track_wind(seq->trk[t], (double)seq->length - (seq->pos + period));
            }
        }
    }

    seq->pos += period;

    if (seq->pos > seq->length)
        seq->pos -= seq->length;
}
