/* timeline.h - Valhalla Tracker (libvht)
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

#ifndef __TIMELINE_H__
#define __TIMELINE_H__

#include "sequence.h"

typedef struct timeslice_t {
	float bpm;
	double length;
	double time;
} timeslice;

typedef struct timechange_t {
	float bpm;
	int linked;
	long row;
} timechange;

typedef struct timestrip_t {
	sequence *seq;
	int start;
	int length;
	int rpb_start;
	int rpb_end;
	int loop_length;
} timestrip;

typedef struct timeline_t {
	timeslice *slices;
	timechange *changes;
	timestrip *strips;
	double *ticks;
	long nslices;
	int nchanges;
	int nstrips;
	int nticks;
	int length;
	double time_length;
	double pos;
	int loop_start;
	int loop_end;

	pthread_mutex_t excl;
} timeline;

timeline *timeline_new(void);
void timeline_free(timeline *tl);
void timeline_update(timeline *tl);
void timeline_advance(timeline *tl, double period);

int timeline_change_set(timeline *tl, long row, float bpm, int linked);
void timeline_change_del(timeline *tl, int id);
char *timeline_get_change(timeline *tl, int id);
int timeline_get_nchanges(timeline *tl);
int timeline_get_nticks(timeline *tl);
double timeline_get_tick(timeline *tl, int n);

timestrip *timeline_get_strip(timeline *tl, int n);
int timeline_get_nstrips(timeline *tl);
timestrip *timeline_add_strip(timeline *tl, sequence *seq, int start, int length, int rpb_start, int rpb_end, int loop_length);
void timeline_del_strip(timeline *tl, int id);

#endif //__TIMELINE_H__
