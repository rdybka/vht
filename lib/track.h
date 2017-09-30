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
#include <pthread.h>
#include "row.h"

#define TRIGGER_NONE 	0
#define TRIGGER_NORMAL 	1
#define TRIGGER_HOLD	2

typedef struct track_t {
    int port;
    int channel;
    int nrows; // actual rows
    int nsrows; // song rows

    double pos;

    int ncols;
    row **rows;
    int *ring;
    int trigger_channel;
    int trigger_note;
    int loop;
    int playing;
    unsigned char trigger_type;
    pthread_mutex_t excl;
} track;

track *track_new(int port, int channel, int len, int songlen);
track *track_clone(track *t);

void track_set_row(track *trk, int c, int n, int type, int note, int velocity, int delay);
int track_get_row(track *trk, int c, int n, row *r);
void track_free(track *);
void track_clear_rows(track *trk, int c);

void track_add_col(track *trk);
void track_del_col(track *trk, int c);
void track_resize(track *trk, int size);

// don't touch those from python
void track_reset(track *trk);
void track_advance(track *trk, double speriod);
void track_wind(track *trk, double speriod);

#endif //__TRACK_H__
