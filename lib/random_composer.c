/* random_composer.c
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
#include <math.h>
#include "random_composer.h"
#include "midi_event.h"

void random_composer_compose(track *trk) {
    // insert random data - should probably get deleted one day
    if (trk->channel == 1) {
        float s = 0;
        for (int n = 0; n < trk->nrows; n+=2) {
            row *r = &trk->rows[0][n];
            r->type = note_on;
            r->note = 64 + (16.0 * (sin(s)));
            r->velocity = 100;

            s += 0.5;

            r = &trk->rows[1][n + 1];
            r->type = note_on;
            r->note = 64 + (16.0 * (sin(s)));
            r->velocity = 100;

            s += 1;
        }
    }

    if (trk->channel == 2) {
        float s = 0;
        for (int n = 0; n < trk->nrows; n+=16) {
            row *r = &trk->rows[0][n];
            r->type = note_on;
            r->note = 64 + (16.0 * (sin(s)));
            r->velocity = 100;

            s += 0.5;

            r = &trk->rows[1][n + 2];
            r->type = note_on;
            r->note = 64 + (16.0 * (sin(s)));
            r->velocity = 100;

            s += 0.3;
        }
    }

}
