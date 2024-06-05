/* timeline.c - vahatraker (libvht)
 *
 * Copyright (C) 2024 Remigiusz Dybka - remigiusz.dybka@gmail.com
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

void ts_should_save(timestrip *ts) {
	if (ts->seq->clt) {
		midi_client *clt = (midi_client *)ts->seq->clt;
		module *mod = (module *)clt->mod_ref;
		mod->should_save = 1;
	}
}

void tl_should_save(timeline *tl) {
	if (tl->clt) {
		midi_client *clt = (midi_client *)tl->clt;
		module *mod = (module *)clt->mod_ref;
		mod->should_save = 1;
	}
}

timeline *timeline_new(midi_client *clt) {
	timeline *ntl = malloc(sizeof(timeline));

	ntl->clt = clt;
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
	ntl->loop_start = -1;
	ntl->loop_end = -1;
	ntl->loop_active = 1;
	timeline_update_inner(ntl);
	ntl->loop_start = 0;
	ntl->loop_end = ntl->length;
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

timechange *timeline_get_change(timeline *tl, int id) {
	timeline_excl_in(tl);
	if ((id == 0) && (!tl->nchanges)) {
		tl->changes = realloc(tl->changes, sizeof(timechange) * ++tl->nchanges);
	}
	timeline_excl_out(tl);
	return &tl->changes[id];
}

timechange *timeline_change_get_at(timeline *tl, long row, int tol) {
	int fc = -1;

	for (int tc = 0; tc < tl->nchanges; tc++) {
		if (tl->changes[tc].row == row)
			return &tl->changes[tc];

		int fuzz = abs(tl->changes[tc].row - row);
		if (fuzz < tol) {
			fc = tc;
			tol = fuzz;
		}
	}

	if (fc >= 0) {
		return &tl->changes[fc];
	}

	return NULL;
}

timechange *timeline_add_change(timeline *tl, float bpm, long row, int linked) {
	timeline_excl_in(tl);
	tl->changes = realloc(tl->changes, sizeof(timechange) * ++tl->nchanges);
	timechange *tc = &tl->changes[tl->nchanges - 1];
	tc->bpm = bpm;
	tc->linked = linked;
	tc->row = row;
	tc->tag = 0;
	timeline_update_inner(tl);
	timeline_excl_out(tl);
	tl_should_save(tl);
	return tc;
}

void timechange_set(timeline *tl, timechange *tc, float bpm, long row, int linked) {
	timeline_excl_in(tl);

	tc->bpm = bpm;
	tc->linked = linked;
	tc->row = row;

	timeline_update_inner(tl);
	timeline_excl_out(tl);
	tl_should_save(tl);
}

void timechange_set_bpm(timeline *tl, timechange *tc, float bpm) {
	timeline_excl_in(tl);
	tc->bpm = bpm;
	timeline_update_inner(tl);
	timeline_excl_out(tl);
	tl_should_save(tl);
}

void timechange_set_row(timeline *tl, timechange *tc, long row) {
	timeline_excl_in(tl);
	tc->row = row;
	timeline_update_inner(tl);
	timeline_excl_out(tl);
	tl_should_save(tl);
}

void timechange_set_linked(timeline *tl, timechange *tc, int linked) {
	timeline_excl_in(tl);
	tc->linked = linked;
	timeline_update_inner(tl);
	timeline_excl_out(tl);
	tl_should_save(tl);
}

float timechange_get_bpm(timechange *tc) {
	return tc->bpm;
}

long timechange_get_row(timechange *tc) {
	return tc->row;
}

int timechange_get_linked(timechange *tc) {
	return tc->linked;
}

void timechange_del(timeline *tl, int id) {
	timeline_excl_in(tl);

	for (int r = id; r < tl->nchanges - 1; r++) {
		tl->changes[r] = tl->changes[r+1];
	}

	tl->changes = realloc(tl->changes, sizeof(timechange) * --tl->nchanges);

	timeline_update_inner(tl);
	timeline_excl_out(tl);
	tl_should_save(tl);
}

float timeline_get_bpm_at_qb(timeline *tl, long row) {
	if (row < tl->nslices)
		return tl->slices[row].bpm;

	timechange *tc = &tl->changes[tl->nchanges - 1];
	if (tc->row == tl->length)
		return tc->bpm;

	return tl->slices[tl->nslices - 1].bpm;
}

int timeline_get_interpol_at_qb(timeline *tl, long row) {
	int chgid = 0;
	int maxr = tl->length + 1;

	for (int c = 0; c < tl->nchanges; c++) {
		timechange *chg = &tl->changes[c];
		if ((chg->row > row) && (chg->row < maxr)) {
			chgid = c;
			maxr = chg->row;
		}
	}

	if (chgid > 0) {
		return tl->changes[chgid].linked;
	}

	return 0;
}


int timeline_get_nticks(timeline *tl) {
	return tl->nticks;
}

double timeline_get_tick(timeline *tl, int n) {
	return tl->ticks[n];
}

void timeline_update_chunk(timeline *tl, int from, int to) {
	long rfrom = tl->changes[from].row;
	float bpmf = tl->changes[from].bpm;
	long rto = tl->length;
	float bpmt = bpmf;

	if (rfrom > tl->nslices)
		return;

	if (to > -1) {
		bpmt = tl->changes[to].bpm;
		rto = tl->changes[to].row;
	}

	//printf("upd: %d -> %d => %ld -> %ld\n", from, to, rfrom, rto);
	float bpmd = (bpmt - bpmf) / (rto - rfrom);
	if (to > -1)
		if (!tl->changes[to].linked)
			bpmd = 0.0;

	if (rto > tl->nslices)
		rto = tl->nslices;

	for (long r = rfrom; r < rto; r++) {
		tl->slices[r].bpm = bpmf;
		bpmf += bpmd;
	}

	if (to > -1)
		if (tl->changes[to].row == 0) {
			tl->slices[0].bpm = tl->changes[to].bpm;
		}
}

void timeline_update(timeline *tl) {
	timeline_excl_in(tl);
	int exp_loop = 0;
	if ((tl->loop_start == 0) && (tl->loop_end == tl->length))
		exp_loop = 1;

	timeline_update_inner(tl);

	if (exp_loop) {
		tl->loop_end = tl->length;
	}

	if (tl->loop_end > tl->length) {
		tl->loop_end = tl->length;
	}

	if (tl->loop_start >= tl->loop_end) {
		tl->loop_start = 0;
	}

	timeline_excl_out(tl);

	for (int c = tl->nchanges -1; c > 0; c--)
		if (tl->changes[c].row > tl->length)
			timechange_del(tl, c);
}

int timechange_compare(const void *a, const void *b) {
	return (int)(((timechange *)a)->row - ((timechange *)b)->row);
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

	qsort(tl->changes, tl->nchanges, sizeof(timechange), timechange_compare);

	tl->slices = realloc(tl->slices, sizeof(timeslice) * tl->length);
	for (int r = 0; r < tl->length; r++) {
		tl->slices[r].time = tl->slices[r].length = tl->slices[r].bpm = 0;
	}
	tl->nslices = tl->length;

	tl->slices[0].time = 0.0;
	tl->nticks = tl->nslices;
	tl->ticks = realloc(tl->ticks, sizeof(double) * (tl->nticks + 1));

	for (int c = 0; c < tl->nchanges - 1; c++) {
		timeline_update_chunk(tl, c, c + 1);
	}

	timeline_update_chunk(tl, tl->nchanges - 1, -1);

	for(int s = 0; s < tl->nslices; s++) {
		tl->slices[s].length = (60.0 / tl->slices[s].bpm) / 4;
		if (s > 0)
			tl->slices[s].time = tl->slices[s - 1].time + tl->slices[s - 1].length;

		tl->ticks[s] = tl->slices[s].time;
	}

	tl->time_length = tl->slices[tl->nslices - 1].time + tl->slices[tl->nslices - 1].length;

	if (tl->pos > tl->length)
		tl->pos = 0;
}

int tick_cmp(const void *t1, const void *t2) {

	double tt1 = *(double* )t1;
	double tt2 = *(double* )t2;

	if ((tt2 - tt1 > 0) && (tt2 - tt1 < 1)) {
		return 0;
	}

	if (tt1 < tt2) {
		return -1;
	}

	if (tt1 > tt2) {
		return 1;
	}

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

	void *rt = bsearch(&t, tl->ticks, tl->nticks, sizeof(double), &tick_cmp);
	if (rt) {
		tstart = (rt - (void *) tl->ticks) / sizeof(double);
	}

	for (int r = tstart; r > -1; r--) {
		if (t > tl->ticks[r])
			return r;
	}

	return -1;
}

double timeline_get_qb_time(timeline *tl, double row) {
	long rr = row;
	double ret = 0.0;

	if (rr < 0)
		return 0;

	if (rr >= tl->nticks) {
		double rl = tl->slices[tl->nticks -1].length;
		ret = tl->ticks[tl->nticks - 1];
		rr -= tl->nticks;
		ret += rl + (rl * rr);
	} else {
		ret = tl->ticks[rr];

		if ((double)rr < row) {
			if (rr < tl->nticks - 1) {
				ret += (row - (double)rr) * (tl->ticks[rr + 1] - tl->ticks[rr]);
			} else {
				ret += tl->slices[tl->nticks -1].length * (row - (double)rr);
			}
		}
	}

	return ret;
}

int timeline_get_room(timeline *tl, int col, long qb, int ig) {
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

int timeline_get_snap(timeline *tl, int tstr_id, long qb_delta) {
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

int timeline_get_strip_for_qb(timeline *tl, int col, long qb) {
	for (int s = 0; s < tl->nstrips; s++)
		if (tl->strips[s].seq->parent == col &&
		        tl->strips[s].start <= qb &&
		        tl->strips[s].start + tl->strips[s].length > qb)
			return s;

	return -1;
}

int timeline_get_last_strip(timeline *tl, int col, long qb) {
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

int timeline_expand(timeline *tl, long qb_start, long qb_n) {
	timeline_excl_in(tl);

	for (int s = 0; s < tl->nstrips; s++) {
		if (tl->strips[s].tag)
			tl->strips[s].start += qb_n;
	}

	for (int c = 0; c < tl->nchanges; c++) {
		if ((tl->changes[c].tag) && (tl->changes[c].row > 0))
			tl->changes[c].row += qb_n;
	}

	if (tl->pos > qb_start)
		tl->pos += qb_n;

	if (tl->loop_start > qb_start)
		tl->loop_start += qb_n;

	if (tl->loop_end > qb_start)
		tl->loop_end += qb_n;

	timeline_update_inner(tl);
	timeline_excl_out(tl);
	tl_should_save(tl);
	return 0;
}

int timeline_expand_start(timeline *tl, long qb) {
	// retag_all
	for (int s = 0; s < tl->nstrips; s++) {
		timestrip *strp = &tl->strips[s];
		int rlen = strp->length;

		if (strp->start >= qb || \
		        (strp->start < qb && strp->start + rlen > qb)) {
			strp->tag = 1;
		} else {
			strp->tag = 0;
		}
	}

	for (int c = 0; c < tl->nchanges; c++) {
		if (tl->changes[c].row >= qb) {
			tl->changes[c].tag = 1;
		} else {
			tl->changes[c].tag = 0;
		}
	}

	int ret = -1;

	// figure out for timechanges
	int minr = 0;
	int maxr = tl->length;

	for (int c = 0; c < tl->nchanges; c++) {
		timechange *tc = &tl->changes[c];
		if ((tc->row < qb) && (tc->row > minr))
			minr = tc->row;

		if ((tc->row >= qb) && (tc->row < maxr))
			maxr = tc->row;
	}

	if (maxr < tl->length)
		ret = maxr - minr - 1;

	// figure out max retract value for strips
	for (int s = 0; s < tl->nstrips; s++) {
		timestrip *strp = &tl->strips[s];

		if (!strp->tag)
			continue;

		if (strp->start < qb)
			qb = strp->start;
	}

	for (int c = 0; c < tl->ncols; c++) {
		int top = qb;
		int bottom = tl->length;

		for (int s = 0; s < tl->nstrips; s++) {
			timestrip *strp = &tl->strips[s];

			if (c != strp->col)
				continue;

			if (strp->start < qb) {
				if (qb - (strp->start + strp->length) < top)
					top = qb - (strp->start + strp->length);
			}

			if (strp->start >= qb)
				if (strp->start - qb < bottom)
					bottom = strp->start - qb;
		}

		if (bottom < tl->length) {
			int gap = top + bottom;
			if (gap < ret || ret == -1)
				ret = gap;
		}
	}

	if (ret == -1)
		return 0;

	return ret;
}

timestrip *timeline_add_strip(timeline *tl, int col, sequence *seq, long start, int length, int rpb_start, int rpb_end) {
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
	s->tag = 0;
	s->seq->index = tl->nstrips - 1;
	s->seq->playing = 0;
	s->seq->pos = 0;
	s->seq->clt = tl->clt;

	s->enabled = 1;

	for (int t = 0; t < s->seq->ntrk; t++) {
		s->seq->trk[t]->clt = tl->clt;
	}

	timeline_update_inner(tl);
	timeline_excl_out(tl);
	tl_should_save(tl);
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
	tl_should_save(tl);
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
	tl_should_save(tl);
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
	tl_should_save(tl);
}

void timeline_reset(timeline *tl) {
	tl->pos = 0;
	for (int s = 0; s < tl->nstrips; s++) {
		tl->strips[s].seq->playing = 0;
	}
}

void timestrip_set_start(timestrip *tstr, int start) {
	tstr->start = start;
	tstr->seq->playing = 0;
	module *mod = ((midi_client *)tstr->seq->clt)->mod_ref;
	timeline *tl = mod->tline;
	timeline_update(tl);
	timeline_update_loops_in_strips(tl);
	tl_should_save(tl);
}

void timestrip_set_length(timestrip *tstr, int length) {
	tstr->length = length;
	tstr->seq->playing = 0;
	module *mod = ((midi_client *)tstr->seq->clt)->mod_ref;
	timeline *tl = mod->tline;
	timeline_update(tl);
	timeline_update_loops_in_strips(tl);
	tl_should_save(tl);
}

double timestrip_get_rpb(timestrip *strp, double offs) {
	double ret = strp->rpb_start;

	double ioffs = trunc(offs);
	double delta = ((double)strp->rpb_end - (double)strp->rpb_start) / strp->length;

	ret = strp->rpb_start + (delta * ioffs);

	if (offs > strp->length)
		ret = strp->rpb_end;

	return ret;
}

void fix_ring_for_new_strip(timeline *tl, timestrip *strp) {
	// this will magically try to pass on ring info
	for (int s = 0; s < tl->nstrips; s++) {
		timestrip *ts = &tl->strips[s];

		if (ts == strp || ts->col != strp->col)
			continue;

		for (int t = 0; t < ts->seq->ntrk; t++) {
			track *trk = ts->seq->trk[t];
			for (int c = 0; c < trk->ncols; c++) {
				if (trk->ring[c] > -1) {
					int passed = 0;

					for (int tt = 0; tt < strp->seq->ntrk && !passed; tt++) {
						track *dtrk = strp->seq->trk[tt];
						if (dtrk->port == trk->port && dtrk->channel == trk->channel) {
							for (int cc = 0; cc < dtrk->ncols; cc++) {
								if (dtrk->ring[cc] == -1) {
									dtrk->ring[cc] = trk->ring[c];
									trk->ring[c] = -1;
									trk->lsounded[c] = -1;
									passed = 1;
								}
							}
						}
					}
				}
			}
		}
	}
}

void timeline_advance_inner(timeline *tl, double period, jack_nframes_t nframes) {
	double len = tl->slices[(long)tl->pos].length;
	double rperiod = period / len;

	double p = ceil(tl->pos) - tl->pos;

	module *mod = (module *)tl->clt->mod_ref;

	if (mod->render_mode == 23)
		return;

	if (rperiod - p > 0.0000001) {
		jack_nframes_t frm = nframes;
		frm *= p / rperiod;
		double sp = p * len;
		period -= sp;
		rperiod -= p;

		if (frm > 0 && frm < nframes) {
			nframes -= frm;
			timeline_advance_inner(tl, sp, frm);
		} else {
			tl->pos = ceil(tl->pos);
		}
	}

	if (tl->pos - floor(tl->pos) < 0.0000001) {	// row boundary
		if (tl->loop_active) {
			if (round(tl->pos) >= tl->loop_end) {
				if (!mod->render_mode || mod->render_mode == 3) {
					if (mod->play_mode == 1) {
						timeline_set_pos(tl, tl->loop_start, 0);
						return;
					}
				} else {
					mod->render_mode = 23;
					mod->end_time = mod->clt->jack_last_frame;
					return;
				}

				//return;
			}
		}

		if (tl->pos == tl->length) {
			for (int s = 0; s < tl->nstrips; s++) {
				timestrip *strp = &tl->strips[s];
				strp->seq->playing = 0;
			}

			//tl->pos = 0;
		}

		// off/on with everything
		for (int s = 0; s < tl->nstrips; s++) {
			timestrip *strp = &tl->strips[s];
			if (!strp->seq->playing) {
				if (strp->start == round(tl->pos) && strp->enabled) {
					strp->seq->pos = 0;
					strp->seq->playing = 1;
					strp->seq->lost = 0;

					fix_ring_for_new_strip(tl, strp);

					for (int t = 0; t < strp->seq->ntrk; t++) {
						track_reset(strp->seq->trk[t]);
					}
				}
			}

			//if (strp->start < tl->pos && (strp->start + sequence_get_relative_length(strp->seq) > tl->pos)) {
			// start mid_strip
			if (strp->enabled && !strp->seq->playing)
				if (strp->start < tl->pos && (strp->start + strp->length > tl->pos)) {
					strp->seq->pos = 0;
					strp->seq->lost = 0;

					long rs = strp->start;
					long re = floor(tl->pos) -1;

					for (long r = rs; r < re; r++) {
						double bpm = tl->slices[r].bpm;
						double rl = tl->slices[r].length;
						strp->seq->pos += rl * timestrip_get_rpb(strp, r - strp->start) * (bpm / 60.0);
					}

					double bpm = tl->slices[re].bpm;
					double rl = tl->slices[re].length;
					strp->seq->pos += rl * timestrip_get_rpb(strp, (double)re - strp->start) * (bpm / 60.0);

					for (int t = 0; t < strp->seq->ntrk; t++) {
						track *trk = strp->seq->trk[t];
						track_reset(trk);
						track_wind(trk, strp->seq->pos);
					}

					strp->seq->playing = 1;
				}
		}
	}

	mod->bpm = timeline_get_bpm_at_qb(tl, (long)tl->pos);
	for (int s = 0; s < tl->nstrips; s++) {
		timestrip *strp = &tl->strips[s];
		double toffi = period * timestrip_get_rpb(strp, tl->pos - strp->start) * (mod->bpm / 60.0);
		int frm = nframes;

		if (strp->seq->playing) {
			double rll = sequence_get_relative_length(strp->seq);

			// finish off seq?
			if ((long)ceil(tl->pos) == (long)(strp->start + strp->length)) {
				if ((strp->seq->pos + toffi) - strp->seq->length > 0.0) {
					if (strp->length == ceil(rll)) {
						double toff = toffi;
						toffi = strp->seq->length - strp->seq->pos;

						frm *= (toffi / toff);
						sequence_advance(strp->seq, toffi, frm);
						toffi = 0.0;
						strp->seq->playing = 0;
					}
				}
			}

			// finish off strip?
			if (strp->seq->playing)
				if ((long)ceil(tl->pos) == (long)(strp->start + strp->length)) {
					//printf("near end: %d %f %ld\n", strp->seq->index, tl->pos, strp->start + strp->length);
					if (tl->pos + rperiod > strp->start + strp->length) {
						double sp = (strp->start + strp->length) - tl->pos;
						frm = nframes;
						frm *= (sp / rperiod);
						sp *= timestrip_get_rpb(strp, tl->pos - strp->start) * (mod->bpm / 60.0);
						sequence_advance(strp->seq, toffi, frm);
						toffi = 0.0;
						strp->seq->playing = 0;
					}
				}


			if (toffi > 0.0) {
				sequence_advance(strp->seq, toffi, frm);
			}
		}
	}

	if (mod->play_mode == 1) {
		for (int s = 0; s < mod->nseq; s++) {
			sequence_advance(mod->seq[s], period * mod->seq[s]->rpb * (mod->bpm / 60.0), mod->clt->jack_buffer_size);
		}
	}

	tl->pos += rperiod;
	if (tl->pos > tl->length) {
		tl->pos = tl->length;
		if (mod->render_mode) {
			mod->render_mode = 23;
			mod->end_time = mod->clt->jack_last_frame;
		}
	}
}

void timeline_advance(timeline *tl, double period, jack_nframes_t nframes) {
	timeline_excl_in(tl);
	timeline_advance_inner(tl, period, nframes);
	timeline_excl_out(tl);
}

int timeline_get_loop_active(timeline *tl) {
	return tl->loop_active;
}

void timeline_set_loop_active(timeline *tl, int val) {
	if (val && tl->pos >= tl->length) {
		timeline_set_pos(tl, tl->loop_start, 0);
	}

	tl->loop_active = val;
	timeline_update_loops_in_strips(tl);
	tl_should_save(tl);
}

long timeline_get_loop_start(timeline *tl) {
	return tl->loop_start;
}

long timeline_get_loop_end(timeline *tl) {
	return tl->loop_end;
}

void timeline_update_loops_in_strips(timeline *tl) {
	for (int s = 0; s < tl->nstrips; s++) {
		timestrip *strp = &tl->strips[s];
		sequence *seq = strp->seq;
		double mtl = sequence_get_relative_length(seq) / seq->length;
		int strplen = ceil((seq->length) * mtl);

		if ((strp->start <= tl->loop_end) && (strp->start + strplen > tl->loop_start) && (tl->loop_active)) {
			int ls = (tl->loop_start - strp->start);
			if (ls > 0) {
				ls /= mtl;
			}

			int le = tl->loop_end - (strp->start + strplen);
			if (le < 0) {
				le /= mtl;
			}

			le += seq->length;
			le--;

			if (ls <= 0 && le >= seq->length - 1) {
				seq->loop_active = 0;
				seq->loop_start = -1;
				seq->loop_end = -1;
			} else {
				seq->loop_start = ls;
				seq->loop_end = le;
				seq->loop_active = 1;
			}
		} else {
			seq->loop_active = 0;
			seq->loop_start = -1;
			seq->loop_end = -1;
		}
	}
}

void timeline_set_loop_start(timeline *tl, long val) {
	tl->loop_start = val;
	timeline_update_loops_in_strips(tl);
	tl_should_save(tl);
}

void timeline_set_loop_end(timeline *tl, long val) {
	tl->loop_end = val;
	timeline_update_loops_in_strips(tl);
	tl_should_save(tl);
}

void timeline_set_pos(timeline *tl, double npos, int let_ring) {
	if (npos >= tl->length || npos < 0)
		return;

	module *mod = (module *)tl->clt->mod_ref;

	tl->pos = npos;
	if (!let_ring)
		for (int s = 0; s < tl->nstrips; s++) {
			sequence *seq = tl->strips[s].seq;

			for (int t = 0; t < seq->ntrk; t++) {
				if (seq->trk[t]->mand->active) {
					mandy_reset(seq->trk[t]->mand);
				}

				if (seq->playing) {
					track_kill_notes(seq->trk[t]);
				}
				seq->playing = 0;
			}
		}

	if (mod->play_mode == 0 || mod->playing == 0) {
		if (tl->loop_active) {
			if (tl->pos > tl->loop_end)
				tl->pos = tl->loop_start;
		}
	}

	// do magic to non-playing seqs in matrix
	int npsl = (int)trunc(npos);
	double ts = tl->slices[npsl].time;
	double remts = tl->slices[npsl].length * (npos - npsl);
	ts += remts;

	if (mod->play_mode == 1) {
		for (int s = 0; s < mod->nseq; s++) {
			sequence *seq = mod->seq[s];
			if (seq->playing)
				continue;

			seq->pos = ts * seq->rpb * 2;
			for (int t = 0; t < seq->ntrk; t++) {
				track_wind(seq->trk[t], seq->pos);
			}

			while(seq->pos > seq->length)
				seq->pos -= seq->length;
		}
	}

	if (mod->transp) {
		jack_nframes_t frames = ts * mod->clt->jack_sample_rate;
		midi_send_transp(mod->clt, mod->playing, frames);
	}
}

double timeline_get_pos(timeline *tl) {
	return tl->pos;
}

int timestrip_get_enabled(timestrip *tstr) {
	return tstr->enabled;
}

void timestrip_set_enabled(timestrip *tstr, int v) {
	tstr->enabled = v;
	sequence *seq = tstr->seq;

	if (!v && seq->playing) {
		for (int t = 0; t < seq->ntrk; t++)
			track_kill_notes(seq->trk[t]);

		seq->playing = 0;
		seq->pos = 0;
	}
}

void timestrip_insert_noteoff(timestrip *tstr, track *src_trk) {
	sequence *seq = tstr->seq;

	int port = src_trk->port;
	int channel = src_trk->channel;
	int ctrlpr = src_trk->ctrlpr;

	int found = -1;
	for (int t = 0; t < seq->ntrk && found == -1; t++) {
		if (seq->trk[t]->port == port && seq->trk[t]->channel == channel) {
			found = t;
		}
	}

	track *trk = NULL;
	if (found > -1) {
		trk = seq->trk[found];
		track_add_col(trk);
		trk->rows[trk->ncols - 1][0].type = note_off;

	} else {
		trk = track_new(port, channel, seq->length, seq->length, ctrlpr);
		trk->rows[0][0].type = note_off;
		sequence_add_track(seq, trk);
	}
}

void timestrip_noteoffise(timeline *tl, timestrip *tstr) {
	sequence *prev = timeline_get_prev_seq(tl, tstr);
	if (!prev)
		return;

	timeline_excl_in(tl);

	for (int t = 0; t < prev->ntrk; t++) {
		for (int c = 0; c < prev->trk[t]->ncols; c++) {
			int found = -1;
			for (int r = prev->trk[t]->nrows - 1; r >= 0 && found == -1; r--) {
				if (prev->trk[t]->rows[c][r].type != none)
					found = r;
			}

			if (found > -1) {
				track *trk = prev->trk[t];
				if (trk->rows[c][found].type == note_on)
					timestrip_insert_noteoff(tstr, trk);
			}

		}
	}

	timeline_excl_out(tl);
}
