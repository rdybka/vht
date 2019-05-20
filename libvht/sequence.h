/* sequence.h - Valhalla Tracker (libvht)
 *
 * Copyright (C) 2019 Remigiusz Dybka - remigiusz.dybka@gmail.com
 * @schtixfnord
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
#include "midi_event.h"
#include "track.h"

#define SEQUENCE_MAX_LENGTH	256

typedef struct sequence_t {
	track **trk;
	int ntrk;
	int length;
	double pos;
	double last_period;
	int midi_focus;
} sequence;

sequence *sequence_new(int length);
void sequence_add_track(sequence *seq, track *trk);
track *sequence_clone_track(sequence *seq, track *trk);
void sequence_set_length(sequence *seq, int length);
void sequence_del_track(sequence *seq, int t);
void sequence_swap_track(sequence *seq, int t1, int t2);
void sequence_double(sequence *seq);
void sequence_halve(sequence *seq);
void sequence_free(sequence *);
void sequence_advance(sequence *seq, double period);

void sequence_handle_record(sequence *seq, midi_event evt);
#endif //__SEQUENCE_H__
