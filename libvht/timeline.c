/* timeline.c - Valhalla Tracker (libvht)
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

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "module.h"

void timeline_excl_in(timeline *tl) {
	pthread_mutex_lock(&tl->excl);
}

void timeline_excl_out(timeline *tl) {
	pthread_mutex_unlock(&tl->excl);
}

timeline *timeline_new(void) {
	timeline *ntl = malloc(sizeof(timeline));

	ntl->slices = NULL;
	ntl->changes = NULL;
	ntl->strips = NULL;
	ntl->ticks = NULL;
	ntl->nchanges = 0;
	ntl->nstrips = 0;
	ntl->nticks = 0;

	ntl->pos = 0.0;
	ntl->length = 32;
	ntl->time_length = 0.0;
	ntl->loop_start = ntl->loop_end = -1;

	pthread_mutex_init(&ntl->excl, NULL);
	return(ntl);
}

void timeline_free(timeline *tl) {
	pthread_mutex_destroy(&tl->excl);
	free(tl->slices);
	free(tl->changes);
	free(tl->ticks);
	free(tl->strips);
	free(tl);
}

int timeline_get_nchanges(timeline *tl) {
	return tl->nchanges;
}

char *timeline_get_change(timeline *tl, int id) {
	static char rc[256];

	if (id > tl->nchanges)
		return NULL;

	if (id < 0)
		return NULL;

	sprintf(rc, "[%lu,%.2f,%d]", tl->changes[id].row, tl->changes[id].bpm, tl->changes[id].linked);
	return rc;
}

int timeline_get_nticks(timeline *tl) {
	return tl->nticks;
}

double timeline_get_tick(timeline *tl, int n) {
	return tl->ticks[n];
}

int timeline_change_id_for_row(timeline *tl, long row) {
	if (tl->nchanges == 0)
		return -1;

	for (int r = 0; r < tl->nchanges; r++)
		if (tl->changes[r].row == row)
			return r;

	return -1;
}

void timeline_update_chunk(timeline *tl, int from, int to) {
	long row = tl->length - 1;
	float bpm = tl->changes[to].bpm;
	int linked = 0;

	if (from > -1) {
		row = tl->changes[from].row;
		bpm = tl->changes[from].bpm;
		linked = tl->changes[from].linked;
	}

	if (row == tl->changes[to].row) {
		return;
	}

	tl->slices[row].bpm = bpm;

	float bpmd = 0;
	if (!linked)
		bpm = tl->changes[to].bpm;

	bpmd = (tl->changes[to].bpm - bpm) / (row - tl->changes[to].row);
	bpm += bpmd;
	for (long r = row - 1; r > tl->changes[to].row; r--) {
		tl->slices[r].bpm = bpm;
		bpm += bpmd;
	}

	if (tl->changes[to].row == 0) {
		tl->slices[0].bpm = tl->changes[to].bpm;
	}
}

void timeline_update(timeline *tl) {
	if (!tl->nchanges)
		return;

	tl->slices = realloc(tl->slices, sizeof(timeslice) * tl->length);
	for (int r = 0; r < tl->length; r++) {
		tl->slices[r].time = tl->slices[r].length = tl->slices[r].bpm = 0;
	}
	tl->nslices = tl->length;

	long lrow = -1;
	int lchange = -1;
	for (int c = 0; c < tl->nchanges; c++) {
		if (tl->changes[c].row > lrow) {
			lrow = tl->changes[c].row;
			lchange = c;
		}
	}

	timeline_update_chunk(tl, -1, lchange);

	long crow = lrow;
	int cchange = lchange;
	lrow = -1;
	while(lchange > -1) {
		lchange = -1;
		lrow = -1;
		for (int c = 0; c < tl->nchanges; c++) {
			if ((tl->changes[c].row > lrow) && (tl->changes[c].row < crow)) {
				lrow = tl->changes[c].row;
				lchange = c;
			}
		}

		if (lchange > -1) {
			timeline_update_chunk(tl, cchange, lchange);
		}

		crow = lrow;
		cchange = lchange;
	}

	for(int s = 0; s < tl->nslices; s++) {
		tl->slices[s].length = 60.0 / tl->slices[s].bpm;
		if (s > 0)
			tl->slices[s].time = tl->slices[s - 1].time + tl->slices[s - 1].length;
	}

	tl->time_length = tl->slices[tl->nslices - 1].time + tl->slices[tl->nslices - 1].length;

	tl->nticks = (int)floor(tl->time_length);
	tl->ticks = realloc(tl->ticks, sizeof(double) * (tl->nticks + 1));

	int last_tick = 0;
	tl->ticks[0] = 0.0;
	for (int r = 0; r < tl->nslices; r++) {
		if ((int)floor(tl->slices[r].time) > last_tick) {
			last_tick++;
			tl->ticks[last_tick] = (double)(r - 1) + (((double)last_tick - tl->slices[r - 1].time) / tl->slices[r - 1].length);
		}
	}
}

void timeline_change_del(timeline *tl, int id) {
	timeline_excl_in(tl);

	for (int r = id; r < tl->nchanges; r++) {
		tl->changes[r] = tl->changes[r+1];
	}

	tl->changes = realloc(tl->changes, sizeof(timechange) * --tl->nchanges);

	timeline_update(tl);
	timeline_excl_out(tl);
}

int timeline_change_set(timeline *tl, long row, float bpm, int linked) {
	timeline_excl_in(tl);

	int r = timeline_change_id_for_row(tl, row);

	if (r == -1) {
		tl->changes = realloc(tl->changes, sizeof(timechange) * ++tl->nchanges);
		r = tl->nchanges - 1;
		tl->changes[r].row = row;
	}

	tl->changes[r].bpm = bpm;
	tl->changes[r].linked = linked;
	timeline_update(tl);
	timeline_excl_out(tl);
	return r;
}

int timeline_get_nstrips(timeline *tl) {
	return tl->nstrips;
}

timestrip *timeline_get_strip(timeline *tl, int n) {
	return &tl->strips[n];
};

timestrip *timeline_add_strip(timeline *tl, sequence *seq, int start, int length, int rpb_start, int rpb_end, int loop_length) {
	timeline_excl_in(tl);

	tl->strips = realloc(tl->strips, sizeof(timestrip) * ++tl->nstrips);
	timestrip *s = &tl->strips[tl->nstrips - 1];
	s->seq = seq;
	s->start = start;
	s->length = length;
	s->rpb_start = rpb_start;
	s->rpb_end = rpb_end;
	s->loop_length = loop_length;

	timeline_excl_out(tl);

	return s;
}

void timeline_del_strip(timeline *tl, int id) {
	timeline_excl_in(tl);

	for (int s = id; s < tl->nstrips; s++) {
		tl->strips[s] = tl->strips[s+1];
	}

	tl->strips = realloc(tl->strips, sizeof(timestrip) * --tl->nstrips);

	timeline_excl_out(tl);
};

void timeline_advance(timeline *tl, double period) {
	timeline_excl_in(tl);
	tl->pos += period;

	timeline_excl_out(tl);
	//printf("%f\n", tl->pos);
}
