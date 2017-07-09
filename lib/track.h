/* track.h
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

#ifndef __TRACK_H__
#define __TRACK_H__

#include "row.h"

#define TRIGGER_NONE 	0
#define TRIGGER_NORMAL 	1
#define TRIGGER_HOLD	2

typedef struct track_t {
	int channel;
	int nrows; // actual rows
	int nsrows; // song rows
	int ncols;
	row **rows;
	int trigger_channel;
	int trigger_note;
	int loop;
	unsigned char trigger_type;
} track;

track *track_new(track *);
void track_free(track *);

#endif //__TRACK_H__
