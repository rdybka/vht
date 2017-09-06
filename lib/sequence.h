/* sequence.h
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

#ifndef __SEQUENCE_H__
#define __SEQUENCE_H__

#include "track.h"

typedef struct sequence_t {
    track **trk;
    int ntrk;
    int length;
} sequence;

sequence *sequence_new();
void sequence_add_track(sequence *, track *);
void sequence_free(sequence *);


#endif //__SEQUENCE_H__