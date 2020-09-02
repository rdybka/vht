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
#include "midi_client.h"
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
	ntl->length = 1024;
	ntl->time_length = 0.0;
	ntl->loop_start = ntl->loop_end = -1;

	timeline_update_inner(ntl);
	pthread_mutex_init(&ntl->excl, NULL);
	return(ntl);
}

void timeline_free(timeline *tl) {
	pthread_mutex_destroy(&tl->excl);
	free(tl->slices);
	free(tl->changes);
	free(tl->ticks);
	for(int s = 0; s < tl->nstrips; s++) {
		sequence_free(tl->strips[s].seq);
	}
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
	timeline_excl_in(tl);
	timeline_update_inner(tl);
	timeline_excl_out(tl);
}

void timeline_update_inner(timeline *tl) {
	tl->length = 32;
	tl->ncols = 0;

	for (int s = 0; s < tl->nstrips; s++) {
		int t = tl->strips[s].start + tl->strips[s].length;
		if (t > tl->length)
			tl->length = t;

		if (tl->strips[s].col + 1 > tl->ncols)
			tl->ncols = tl->strips[s].col + 1;
	}

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

	tl->slices[0].time = 0.0;
	tl->nticks = tl->nslices;
	tl->ticks = realloc(tl->ticks, sizeof(double) * (tl->nticks + 1));

	for(int s = 0; s < tl->nslices; s++) {
		tl->slices[s].length = (60.0 / tl->slices[s].bpm) / 4;
		if (s > 0)
			tl->slices[s].time = tl->slices[s - 1].time + tl->slices[s - 1].length;

		tl->ticks[s] = tl->slices[s].time;
	}

	tl->time_length = tl->slices[tl->nslices - 1].time + tl->slices[tl->nslices - 1].length;
}

int tick_cmp(const void *t1, const void *t2) {

	double tt1 = *(double* )t1;
	double tt2 = *(double* )t2;

	if ((tt2 - tt1 > 0) && (tt2 - tt1 < 5))
		return 0;

	if (tt1 < tt2)
		return -1;

	if (tt1 > tt2)
		return 1;

	return 0;
}

long timeline_get_qb(timeline *tl, double t) {
	if (t > tl->time_length) { // past end
		double extra_time = t - tl->time_length;
		double tlen = tl->ticks[tl->nticks - 1] - tl->ticks[tl->nticks - 2];
		return tl->nticks + (long)floor(extra_time / tlen);
	}

	if (t == 0.0)
		return 0;

	if (t < 0) {
		return (long)floor(t / tl->ticks[1]);
	}

	long tstart = tl->nticks - 1;

	void *rt = bsearch(&t, tl->ticks, sizeof(double), tl->nticks, &tick_cmp);
	if (rt) {
		tstart = (rt - (void *) tl->ticks) / sizeof(double);
	}

	for (int r = tstart; r > -1; r--) {
		if (t > tl->ticks[r])
			return r;
	}

	return -1;
}

double timeline_get_qb_time(timeline *tl, long row) {
	long rr = row;

	if (rr < 0)
		return 0;

	if (rr >= tl->nticks -1) {
		double t = tl->ticks[tl->nticks -1];
		double rl = tl->slices[tl->nticks -1].length;
		rr -= tl->nticks;

		return t + rl + (rl * rr);
	}

	return tl->ticks[rr];
}

void timeline_change_del(timeline *tl, int id) {
	timeline_excl_in(tl);

	for (int r = id; r < tl->nchanges; r++) {
		tl->changes[r] = tl->changes[r+1];
	}

	tl->changes = realloc(tl->changes, sizeof(timechange) * --tl->nchanges);

	timeline_update_inner(tl);
	timeline_excl_out(tl);
}

int timeline_get_room(timeline *tl, int col, int qb, int ig) {
	if (col < 0)
		return 0;

	int ret = -1;

	if (qb < 0)
		qb = 0;

	for (int s = 0; s < tl->nstrips; s++) {
		if (s == ig)
			continue;

		if (tl->strips[s].col == col) {
			int rm = tl->strips[s].start - qb;

			if (rm <= 0 && tl->strips[s].start + tl->strips[s].length > qb)
				return 0;

			if (rm > 0 && (rm < ret || ret == -1))
				ret = rm;
		}
	}

	if (qb >= tl->length) {
		ret = -1;
	}

	return ret;
}

int timeline_get_snap(timeline *tl, int tstr_id, int qb_delta) {
	timestrip *tstr = &tl->strips[tstr_id];
	int ret = tstr->start;

	if (tstr->start + qb_delta >= tl->length) { // past end
		ret += qb_delta;
		return ret;
	}

	// is pos valid?
	int rm = timeline_get_room(tl, tstr->col, tstr->start + qb_delta, tstr_id);
	if (rm == -1) { // last
		ret += qb_delta;
	}

	if (rm >= tstr->length) { // there's room
		ret += qb_delta;
	} else {
		int np = tstr->start + qb_delta;
		if (qb_delta > 0) {// snap from top
			np -= tstr->length - rm;
			rm = timeline_get_room(tl, tstr->col, np, tstr_id);
			if (rm >= tstr->length)
				ret = np;
		} else { // snap from bottom
			int strp = timeline_get_strip_for_qb(tl, tstr->col, np);

			if (strp > -1 && strp != tstr_id) {
				np = tl->strips[strp].start + tl->strips[strp].length;
				rm = timeline_get_room(tl, tstr->col, np, tstr_id);
				if (rm >= tstr->length || rm == -1)
					ret = np;
			}
		}
	}

	if (ret < 0)
		ret = 0;

	//printf("snap: %d %d -> %d\n", tstr_id, qb_delta, ret);
	return ret;
}

int timeline_place_clone(timeline *tl, int tstr_id) {
	timestrip *tstr = &tl->strips[tstr_id];
	int ret = tstr->start + tstr->length;

	int oldret = -1;

	while(oldret != ret) {
		oldret = ret;
		int rm = timeline_get_room(tl, tstr->col, ret, -1);
		if (rm >= tstr->length || rm == -1) {
			break;
		} else {
			ret += rm;

			int next = timeline_get_strip_for_qb(tl, tstr->col, ret);
			if (next == -1)
				break;

			timestrip *nstr = &tl->strips[next];
			ret = nstr->start + nstr->length;
		}
	}

	return ret;
}

int timestrip_can_resize_seq(timeline *tl, timestrip *tstr, int len) {
	int ret = 0;
	int index = tstr->seq->index;
	sequence *seq = tstr->seq;

	int rlen = (int)ceil((4.0 / (double)seq->rpb) * len);

	int rm = timeline_get_room(tl, tstr->col, tstr->start, index);
	if (rm >= rlen || rm == -1) {
		ret = 1;
	}

	return ret;
}


int timestrip_can_rpb_seq(timeline *tl, timestrip *tstr, int rpb) {
	int ret = 0;

	int index = tstr->seq->index;
	sequence *seq = tstr->seq;

	int rlen = (int)ceil((4.0 / (double)rpb) * seq->length);

	int rm = timeline_get_room(tl, tstr->col, tstr->start, index);
	if (rm >= rlen || rm == -1) {
		ret = 1;
	}

	return ret;
}

sequence *timeline_get_prev_seq(timeline *tl, timestrip *tstr) {
	sequence *ret = NULL;

	if (tstr->seq->parent == -1) {
		return ret;
	}

	int maxr = -1;

	for (int s = 0; s < tl->nstrips; s++) {
		if (tl->strips[s].col == tstr->col) {
			timestrip *st = &tl->strips[s];

			if (st->start > maxr) {
				if (st->start < tstr->start) {
					ret = tl->strips[s].seq;
					maxr = st->start;
				}
			}
		}
	}

	if (ret == tstr->seq)
		return NULL;

	return ret;
}

sequence *timeline_get_next_seq(timeline *tl, timestrip *tstr) {
	return NULL;
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
	timeline_update_inner(tl);
	timeline_excl_out(tl);
	return r;
}

int timeline_get_nstrips(timeline *tl) {
	return tl->nstrips;
}

timestrip *timeline_get_strip(timeline *tl, int n) {
	return &tl->strips[n];
};

sequence *timeline_get_seq(timeline *tl, int n) {
	if (n < 0 || n >= tl->nstrips)
		return 0;

	return tl->strips[n].seq;
}

int timeline_get_strip_for_qb(timeline *tl, int col, int qb) {
	for (int s = 0; s < tl->nstrips; s++)
		if (tl->strips[s].seq->parent == col &&
		        tl->strips[s].start <= qb &&
		        tl->strips[s].start + tl->strips[s].length > qb)
			return s;

	return -1;
}

int timeline_get_last_strip(timeline *tl, int col, int qb) {
	int ret = -1;
	int max_r = -1;

	for (int s = 0; s < tl->nstrips; s++) {
		if (tl->strips[s].col == col) {
			if (tl->strips[s].start > max_r && tl->strips[s].start < qb) {
				max_r = tl->strips[s].start;
				ret = s;
			}
		}
	}

	return ret;
}

int timeline_get_max_contract(timeline *tl, int qb) {
	int ret = qb;

	for (int s = 0; s < tl->nstrips; s++) {
		timestrip *strp = &tl->strips[s];

		if (strp->start < qb && strp->start + strp->length >= qb) // inside a strip!
			return 0;

		if (strp->start < qb) {
			if (qb - (strp->start + strp->length) < ret)
				ret = qb - (strp->start + strp->length);
		}
	}

	return ret;
}

int timeline_expand(timeline *tl, int qb_start, int qb_n) {
	timeline_excl_in(tl);

	for (int s = 0; s < tl->nstrips; s++) {
		if (tl->strips[s].start >= qb_start)
			tl->strips[s].start += qb_n;
	}

	timeline_update_inner(tl);
	timeline_excl_out(tl);
	return 0;
}


timestrip *timeline_add_strip(timeline *tl, int col, sequence *seq, int start, int length, int rpb_start, int rpb_end) {
	timeline_excl_in(tl);

	int maxid = -1;
	for (int t = 0; t < tl->nstrips; t++)
		if (tl->strips[t].col == col)
			if (tl->strips[t].seq->index > maxid)
				maxid = tl->strips[t].seq->index;

	tl->strips = realloc(tl->strips, sizeof(timestrip) * ++tl->nstrips);
	timestrip *s = &tl->strips[tl->nstrips - 1];
	s->seq = seq;
	s->seq->parent = col;
	s->start = start;
	s->length = length;
	s->rpb_start = rpb_start;
	s->rpb_end = rpb_end;
	s->col = col;
	s->seq->index = tl->nstrips - 1;
	s->seq->playing = 0;
	s->seq->pos = 0;

	timeline_update_inner(tl);
	timeline_excl_out(tl);
	return s;
}

void timeline_del_strip(timeline *tl, int id) {
	timeline_excl_in(tl);

	sequence_free(tl->strips[id].seq);
	for (int s = id; s < tl->nstrips - 1; s++) {
		tl->strips[s] = tl->strips[s+1];
		tl->strips[s].seq->index = s;
	}

	tl->strips = realloc(tl->strips, sizeof(timestrip) * --tl->nstrips);

	timeline_excl_out(tl);
}

void timeline_delete_all_strips(timeline *tl, int col) {
	for (int s = 0; s < tl->nstrips; s++) {
		if (tl->strips[s].col == col) {
			sequence_free(tl->strips[s].seq);
			for (int ss = s; ss < tl->nstrips - 1; ss++) {
				tl->strips[ss] = tl->strips[ss+1];
				tl->strips[ss].seq->index = ss;
			}

			tl->strips = realloc(tl->strips, sizeof(timestrip) * --tl->nstrips);
			s--;

		}
	}

	for (int s = 0; s < tl->nstrips; s++) {
		if (tl->strips[s].col > col) {
			tl->strips[s].col--;
			tl->strips[s].seq->parent = tl->strips[s].col;
		}
	}
}

void timeline_clear(timeline *tl) {
	timeline_excl_in(tl);

	for (int s = 0; s < tl->nstrips; s++) {
		sequence_free(tl->strips[s].seq);
	}

	if (tl->strips)
		free(tl->strips);
	tl->nstrips = 0;
	tl->strips = NULL;

	if (tl->changes)
		free(tl->changes);
	tl->nchanges = 0;
	tl->changes = NULL;

	if (tl->ticks)
		free(tl->ticks);
	tl->nticks = 0;
	tl->ticks = NULL;

	timeline_update_inner(tl);
	timeline_excl_out(tl);

}

void timeline_swap_sequence(timeline *tl, int s1, int s2) {
	timeline_excl_in(tl);
	s1++;
	s2++;

	for (int st = 0; st < tl->nstrips; st++) {
		tl->strips[st].col++;
		tl->strips[st].seq->parent++;
	}

	for (int st = 0; st < tl->nstrips; st++) {
		if (tl->strips[st].col == s1)
			tl->strips[st].col = -s2;
		if (tl->strips[st].col == s2)
			tl->strips[st].col = -s1;

		if (tl->strips[st].seq->parent == s1)
			tl->strips[st].seq->parent = -s2;
		if (tl->strips[st].seq->parent == s2)
			tl->strips[st].seq->parent = -s1;
	}

	for (int st = 0; st < tl->nstrips; st++) {
		if (tl->strips[st].col == -s1)
			tl->strips[st].col = s1;
		if (tl->strips[st].col == -s2)
			tl->strips[st].col = s2;
		if (tl->strips[st].seq->parent == -s1)
			tl->strips[st].seq->parent = s1;
		if (tl->strips[st].seq->parent == -s2)
			tl->strips[st].seq->parent = s2;
	}

	for (int st = 0; st < tl->nstrips; st++) {
		tl->strips[st].col--;
		tl->strips[st].seq->parent--;
	}

	timeline_excl_out(tl);
}

void timeline_advance(timeline *tl, double period) {
	timeline_excl_in(tl);
	tl->pos += period;

	timeline_excl_out(tl);
	//printf("%f\n", tl->pos);
}
