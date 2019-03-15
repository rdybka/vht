/* track.c
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

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <math.h>

#include "jack_client.h"
#include "module.h"
#include "track.h"
#include "row.h"
#include "libvht.h"

track *track_new(int port, int channel, int len, int songlen) {
	track *trk = malloc(sizeof(track));
	if (len == -1)
		len = module.def_nrows;

	if (songlen == -1)
		songlen = len;

	trk->channel = channel;
	trk->nrows = len;
	trk->arows = len;
	trk->nsrows = songlen;
	trk->trigger_channel = 0;
	trk->trigger_note = 0;
	trk->loop = 1;
	trk->trigger_type = TRIGGER_NORMAL;
	trk->ncols = 1;
	trk->playing = 0;
	trk->port = port;
	trk->cur_rec_update = 0;
	trk->resync = 1;
	pthread_mutex_init(&trk->excl, NULL);
	pthread_mutex_init(&trk->exclrec, NULL);
	pthread_mutex_init(&trk->exclctrl, NULL);

	trk->rows = malloc(sizeof(row*) * trk->ncols);
	trk->ring = malloc(sizeof(int) * trk->ncols);
	for (int c = 0; c < trk->ncols; c++) {
		trk->rows[c] = malloc(sizeof(row) * trk->nrows);
		track_clear_rows(trk, c);

		trk->ring[c] = -1;
	}

	trk->ctrlpr = TRACK_CONTROLS_PER_ROW;
	trk->nctrl = 0;
	trk->ctrl = 0;
	trk->ctrlnum = 0;
	trk->lctrlval = 0;
	trk->env = 0;

	trk->crows = 0;

	track_add_ctrl(trk, -1);
	track_reset(trk);
	trk->playing = 1;
	return trk;
};

void track_reset(track *trk) {
	trk->pos = trk->last_pos = trk->last_period = 0.0;
	track_kill_notes(trk);
}

void track_set_row(track *trk, int c, int n, int type, int note, int velocity, int delay) {
	pthread_mutex_lock(&trk->excl);

	row *r = &trk->rows[c][n];
	r->type = type;
	r->note = note;
	r->velocity = velocity;
	r->delay = delay;
	r->ringing = 0;

	for (int c = 0; c < trk->nctrl; c++)
		trk->lctrlval[c] = -1;

	pthread_mutex_unlock(&trk->excl);
	track_insert_rec_update(trk, c, n);
}

void track_set_wanderer(track *trk, int c, int p, int v) {
	pthread_mutex_lock(&trk->excl);
	row *r = &trk->rows[c][p];
	r->ringing = v;
	pthread_mutex_unlock(&trk->excl);
}

int track_get_row(track *trk, int c, int n, row *r) {
	if ((c >= trk->ncols) || (n >= trk->nrows)) {
		fprintf(stderr, "Invalid track address [%d:%d]\n", c, n);
		return -1;
	}

	if (r == NULL) {
		fprintf(stderr, "Destination row==NULL\n");
		return -1;
	}

	pthread_mutex_lock(&trk->excl);

	row *s = &trk->rows[c][n];
	r->type = s->type;
	r->note = s->note;
	r->velocity = s->velocity;
	r->delay = s->delay;
	r->ringing = s->ringing;

	pthread_mutex_unlock(&trk->excl);
	return 0;
}

void track_set_ctrl(track *trk, int c, int n, int val) {
	pthread_mutex_lock(&trk->exclctrl);

	trk->ctrl[c][n] = val;

	// pitch wheel is a bit trickier
	if (trk->ctrlnum[c] == -1) {
		if (val == 64 * 128) {
			int disc = 0;
			for (int r = 0; r < trk->nrows * trk->ctrlpr; r++) {
				if (trk->ctrl[c][r] == 64 * 128) {
					if (disc == 0) {
						disc = 1;
					} else {
						trk->ctrl[c][r] = -1;
					}
				} else if (trk->ctrl[c][r] > -1) {
					disc = 0;
				}
			}
		}
	}

	pthread_mutex_unlock(&trk->exclctrl);

	track_insert_rec_update(trk, c + trk->ncols, n / trk->ctrlpr);
}

char *track_get_ctrl_nums(track *trk) {
	static char rc[256];
	pthread_mutex_lock(&trk->exclctrl);

	sprintf(rc, "[");
	for (int c = 0; c < trk->nctrl; c++) {
		char buff[32];
		sprintf(buff, "%d,", trk->ctrlnum[c]);
		strcat(rc, buff);
	}

	strcat(rc, "]");

	pthread_mutex_unlock(&trk->exclctrl);
	return rc;
}

void track_set_ctrl_num(track *trk, int c, int v) {
	pthread_mutex_lock(&trk->exclctrl);
	trk->ctrlnum[c] = v;
	pthread_mutex_unlock(&trk->exclctrl);
}

// as played
void track_get_ctrl(track *trk, int *ret, int l, int c, int n) {
	int ll = 0;
	pthread_mutex_lock(&trk->exclctrl);
	if (trk->nctrl > 0) {
		for (int nn = n * trk->ctrlpr; nn < (n + 1) * trk->ctrlpr; nn++) {
			int v = trk->ctrl[c][nn];

			if (v == -1) {
				v = env_get_v(trk->env[c],  trk->ctrlpr, (float)nn / (float)trk->ctrlpr);
				if ((v > -1) && (c == 0)) // pitchwheel
					v *= 128;
			}

			if (ll < l)
				ret[ll++] = v;
		}
	}

	pthread_mutex_unlock(&trk->exclctrl);
}

// doodles
void track_get_ctrl_rec(track *trk, int *ret, int l, int c, int n) {
	int ll = 0;
	pthread_mutex_lock(&trk->exclctrl);

	if (trk->nctrl > 0) {
		for (int nn = n * trk->ctrlpr; nn < (n + 1) * trk->ctrlpr; nn++) {
			if (ll < l)
				ret[ll++] = trk->ctrl[c][nn];
		}
	}

	pthread_mutex_unlock(&trk->exclctrl);
}

// env
void track_get_ctrl_env(track *trk, int *ret, int l, int c, int n) {
	int ll = 0;
	pthread_mutex_lock(&trk->exclctrl);

	if (trk->nctrl > 0) {
		for (int nn = n * trk->ctrlpr; nn < (n + 1) * trk->ctrlpr; nn++) {
			int v = env_get_v(trk->env[c],  trk->ctrlpr, (float)nn / (float)trk->ctrlpr);

			if ((v > -1) && (c == 0)) // pitchwheel
				v *= 128;

			if (ll < l)
				ret[ll++] = v;

		}
	}

	pthread_mutex_unlock(&trk->exclctrl);
}


void track_free(track *trk) {
	pthread_mutex_destroy(&trk->excl);
	pthread_mutex_destroy(&trk->exclrec);
	pthread_mutex_destroy(&trk->exclctrl);

	for (int c = 0; c < trk->ncols; c++) {
		free(trk->rows[c]);
	}

	for (int c = 0; c < trk->nctrl; c++) {
		free(trk->ctrl[c]);
		envelope_free(trk->env[c]);
		free(trk->crows[c]);
	}

	free(trk->crows);
	free(trk->ring);
	free(trk->rows);
	free(trk->ctrl);
	free(trk->ctrlnum);
	free(trk->lctrlval);
	free(trk->env);

	free(trk);
}

void track_clear_rows(track *trk, int c) {
	pthread_mutex_lock(&trk->excl);

	for (int t = 0; t < trk->nrows; t++) {
		trk->rows[c][t].type = none;
		trk->rows[c][t].note = 0;
		trk->rows[c][t].velocity = 0;
		trk->rows[c][t].delay = 0;
		trk->rows[c][t].ringing = 0;
	}

	pthread_mutex_unlock(&trk->excl);
}

void track_clear_crows(track *trk, int c) {
	pthread_mutex_lock(&trk->exclctrl);

	for (int t = 0; t < trk->nrows; t++) {
		trk->crows[c][t].velocity = -1;
		trk->crows[c][t].linked = 0;
	}

	pthread_mutex_unlock(&trk->exclctrl);
}

track *track_clone(track *src) {
	track *dst = track_new(src->port, src->channel, src->nrows, src->nsrows);

	for (int c = 0; c < src->ncols; c++) {
		if (c > 0)
			track_add_col(dst);

		for (int r = 0; r < src->nrows; r++) {
			row *s = &src->rows[c][r];
			row_set(&dst->rows[c][r], s->type, s->note, s->velocity, s->delay);
		}
	}

	for (int c = 0; c < src->nctrl; c++) {
		if (c > 0)
			track_add_ctrl(dst, src->ctrlnum[c]);

		for (int r = 0; r < src->nrows; r++) {
			ctrlrow *s = &src->crows[c][r];
			ctrlrow_set(&dst->crows[c][r], s->velocity, s->linked, s->smooth, s->anchor);

			for (int rr = 0; rr < src->ctrlpr; rr++) {
				dst->ctrl[c][(r * src->ctrlpr) + rr] = src->ctrl[c][(r * src->ctrlpr) + rr]	;
			}
		}

		track_ctrl_refresh_envelope(dst, c);

		// don't forget about the triggers one day!!!!
	}

	return dst;
}

int col_free(track *trk, int col, int pos) {
	if (col >= trk->ncols)
		return 0;

	// since we only read, ignore thread safety
	int ret = 1;

	int found = 0;
	for (int y = pos; y >= 0 && !found; y--) {
		if (trk->rows[col][y].type == note_on) {
			found = 1;
			ret = 0;
		}

		if (trk->rows[col][y].type == note_off) {
			found = 1;
		}
	}

	if (!found) {
		for (int y = trk->nrows - 1; y > pos && !found; y--) {
			if (trk->rows[col][y].type == note_on) {
				found = 1;
				ret = 0;
			}

			if (trk->rows[col][y].type == note_off) {
				found = 1;
			}
		}
	}

	return ret;
}

int track_get_wandering_note(track *trk, int c, int pos) {
	int ret = -1;

	if (c >= trk->ncols)
		return ret;

	// since we only read, ignore thread safety
	int found = 0;
	for (int y = pos - 1; y >= 0 && !found; y--) {
		if (trk->rows[c][y].type == note_on) {
			found = 1;
			if (trk->rows[c][y].ringing) {
				ret = y;
			}
		}

		if (trk->rows[c][y].type == note_off) {
			found = 1;
		}
	}

	if (!found) {
		for (int y = trk->nrows - 1; y > pos && !found; y--) {
			if (trk->rows[c][y].type == note_on) {
				found = 1;
				if (trk->rows[c][y].ringing) {
					ret = y;
				}
			}

			if (trk->rows[c][y].type == note_off) {
				found = 1;
			}
		}
	}

	return ret;
}

int col_last_note(track *trk, int col, double pos) {
	// since we only read, ignore thread safety
	if (col >= trk->ncols)
		return -1;

	if (trk->rows[col][(int)pos].type == note_on) {
		return trk->rows[col][(int)pos].note;
	}

	if (trk->rows[col][(int)pos].type == note_off) {
		return -1;
		//return trk->rows[col][(int)pos].note;
	}

	int ret = -1;

	int found = 0;
	for (int y = pos; y >= 0 && !found; y--) {
		if (trk->rows[col][y].type == note_on) {
			found = 1;
			ret = trk->rows[col][y].note;
		}

		if (trk->rows[col][y].type == note_off) {
			found = 1;
		}
	}

	if (!found) {
		for (int y = trk->nrows - 1; y > pos && !found; y--) {
			if (trk->rows[col][y].type == note_on) {
				found = 1;
				ret = trk->rows[col][y].note;
			}

			if (trk->rows[col][y].type == note_off) {
				found = 1;
			}
		}
	}

	return ret;
}

// yooohoooo!!!
void track_play_row(track *trk, int pos, int c, int delay) {
	row r;
	track_get_row(trk, c, pos, &r);

	if (r.type == none)
		return;

	midi_event evt;

	if (r.type == note_on || r.type == note_off ) {
		if (trk->ring[c] != -1) {
			evt.time = delay;
			evt.channel = trk->channel;
			evt.type = note_off;
			evt.note = trk->ring[c];
			evt.velocity = 0;
			midi_buffer_add(trk->port, evt);
			trk->ring[c] = -1;
		}
	}

	if (r.type != note_off) {
		evt.time = delay;
		evt.channel = trk->channel;
		evt.type = r.type;
		evt.note = r.note;
		evt.velocity = r.velocity;
		midi_buffer_add(trk->port, evt);

		// fix wandering notes
		int wanderer = track_get_wandering_note(trk, c, pos);
		if (wanderer > -1) {
			int found = 0;
			int dest_col = 0;

			for (int cc = 0; cc < trk->ncols && !found; cc++) {
				int ln = col_last_note(trk, cc, pos);

				if (ln == -1) {
					found = 1;
					dest_col = cc;
				}
			}

			if (!found) {
				track_add_col(trk);
				dest_col = trk->ncols - 1;
			}

			// copy wanderer to new position
			row r;
			track_get_row(trk, c, wanderer, &r);
			track_set_row(trk, c, wanderer, none, 0, 0, 0);
			track_set_row(trk, dest_col, wanderer, r.type, r.note, r.velocity, r.delay);
			track_set_wanderer(trk, dest_col, wanderer, 1);
		}

	}

	if (r.type == note_on) {
		trk->ring[c] = r.note;
		track_set_wanderer(trk, c, pos, 0);
	}
}

void track_advance(track *trk, double speriod) {
	// length of period in track time
	double tperiod = ((double)trk->nrows / (double)trk->nsrows) * speriod;
	double tmul = (double) jack_buffer_size / tperiod;

	int row_start = floorf(trk->pos);
	int row_end = floorf(trk->pos + tperiod) + 1;

	if (row_end > trk->nrows)
		row_end = trk->nrows;

	// play notes
	for (int c = 0; c < trk->ncols; c++)
		for (int n = row_start; n <= row_end; n++) {
			int nn = n;

			if (trk->loop)
				if (nn >= trk->nrows)
					nn = 0;

			if (nn < trk->nrows) {
				row r;
				track_get_row(trk, c, nn, &r);

				double trigger_time = (double)n + ((double)r.delay / 49.0);
				double delay = trigger_time - trk->pos;
				if ((delay >= 0) && (delay < tperiod)) {
					if (trk->playing) {
						track_play_row(trk, nn, c, delay * tmul);
						//printf("note: %f %f %f %d %d\n", trigger_time, trk->pos, delay, row_start, row_end);
					}
				}
			}
		}

	// play controllers
	int ctrlfrom = (trk->pos / trk->nrows) * trk->nrows * trk->ctrlpr;
	int ctrlto = ((trk->pos + tperiod)  / trk->nrows) * trk->nrows * trk->ctrlpr;

	if (ctrlto == ctrlfrom)
		ctrlto += 1;

	double cper = tperiod / (ctrlto - ctrlfrom);
	for (int c = 0; c < trk->nctrl; c++) {
		for (int r = ctrlfrom; r <= ctrlto; r++) {
			int rr = r;

			while(rr >= trk->nrows * trk->ctrlpr)
				rr -= trk->nrows * trk->ctrlpr;

			double delay = ((double)r / trk->ctrlpr) - trk->pos;

			int ctrl = trk->ctrlnum[c];

			float dt = env_get_v(trk->env[c],  trk->ctrlpr, (float)rr / (float)trk->ctrlpr);
			int data = dt;

			if ((data > -1) && (c == 0)) // pitchwheel
				data = dt * 128;

			if (data == -1) {
				data = trk->ctrl[c][rr];
			}

			if (data > -1) {
				midi_event evt;

				evt.time = delay * tmul;
				evt.channel = trk->channel;
				evt.type = control_change;
				evt.control = ctrl;
				evt.data = data;

				if (ctrl == -1) {
					evt.type = pitch_wheel;
					evt.msb = data / 128;
					evt.lsb = data - (evt.msb * 128);
				}

				if ((delay >= 0) && (delay < tperiod)) {
					if (trk->playing)
						if (data != trk->lctrlval[c]) {
							trk->lctrlval[c] = data;
							midi_buffer_add(trk->port, evt);
						}
				}
			}

			delay += cper;
		}
	}

	trk->last_pos = trk->pos;
	trk->last_period = tperiod;
	trk->pos += tperiod;

	if (trk->loop) {
		if (trk->pos > trk->nrows)
			trk->pos -= trk->nrows;
	}
}

void track_wind(track *trk, double period) {
	double tperiod = ((double)trk->nrows / (double)trk->nsrows) * period;
	trk->pos += tperiod;
}

void track_kill_notes(track *trk) {
	for (int c = 0; c < trk->ncols; c++) {
		if (trk->ring[c] != -1) {
			queue_midi_note_off(0, 0, trk->channel, trk->ring[c]);

			trk->ring[c] = -1;
		}

		pthread_mutex_lock(&trk->excl);

		for (int t = 0; t < trk->nrows; t++) {
			trk->rows[c][t].ringing = 0;
		}

		pthread_mutex_unlock(&trk->excl);
	}
}

void track_ctrl_refresh_envelope(track *trk, int c) {
	envelope_regenerate(trk->env[c], trk->crows[c]);
}

void track_add_col(track *trk) {
	pthread_mutex_lock(&trk->excl);
	trk->ncols++;

	trk->rows = realloc(trk->rows, sizeof(row*) * trk->ncols);
	trk->rows[trk->ncols -1] = malloc(sizeof(row) * trk->arows);
	trk->ring = realloc(trk->ring, sizeof(int) * trk->ncols);
	pthread_mutex_unlock(&trk->excl);

	track_clear_rows(trk, trk->ncols - 1);
}

void track_add_ctrl(track *trk, int c) {
	pthread_mutex_lock(&trk->exclctrl);
	trk->nctrl++;

	trk->ctrl = realloc(trk->ctrl, sizeof(int*) * trk->nctrl);
	trk->ctrl[trk->nctrl -1] = malloc(sizeof(int)  * trk->ctrlpr * trk->arows);
	trk->ctrlnum = realloc(trk->ctrlnum, sizeof(int) * trk->nctrl);
	trk->ctrlnum[trk->nctrl -1] = c;
	trk->lctrlval = realloc(trk->lctrlval, sizeof(int) * trk->nctrl);
	if (c == 0) {
		trk->lctrlval[trk->nctrl -1] = 64 * 127;
	} else {
		trk->lctrlval[trk->nctrl -1] = -1;
	}
	trk->env = realloc(trk->env, sizeof(envelope *) * trk->nctrl);
	trk->env[trk->nctrl -1] = envelope_new(trk->nrows, trk->ctrlpr);

	trk->crows = realloc(trk->crows, sizeof(ctrlrow *) * trk->nctrl);
	trk->crows[trk->nctrl - 1] = malloc(sizeof(ctrlrow) * trk->arows);

	for (int r = 0; r < trk->ctrlpr * trk->arows; r++) {
		trk->ctrl[trk->nctrl -1][r] = -1;
	}

	pthread_mutex_unlock(&trk->exclctrl);

	track_clear_crows(trk, trk->nctrl - 1);
}

void track_del_col(track *trk, int c) {
	if ((c >= trk->ncols) || (c < 0) || (trk->ncols == 1)) {
		return;
	}

	module_excl_in();

	for (int cc = c; cc < trk->ncols - 1; cc++) {
		trk->rows[cc] = trk->rows[cc+1];
		trk->ring[cc] = trk->ring[cc+1];
	}

	trk->ncols--;

	trk->rows = realloc(trk->rows, sizeof(row*) * trk->ncols);
	trk->ring = realloc(trk->ring, sizeof(int) * trk->ncols);

	module_excl_out();
}

void track_del_ctrl(track *trk, int c) {
	if ((c >= trk->nctrl) || (c < 0)) {
		return;
	}

	pthread_mutex_lock(&trk->exclctrl);

	free(trk->crows[c]);
	free(trk->ctrl[c]);
	envelope_free(trk->env[c]);

	for (int cc = c; cc < trk->nctrl - 1; cc++) {
		trk->ctrl[cc] = trk->ctrl[cc+1];
		trk->ctrlnum[cc] = trk->ctrlnum[cc+1];
		trk->env[cc] = trk->env[cc+1];
		trk->crows[cc] = trk->crows[cc + 1];
	}

	trk->nctrl--;

	trk->crows = realloc(trk->crows, sizeof(ctrlrow *) * trk->nctrl);
	trk->ctrl = realloc(trk->ctrl, sizeof(int*) * trk->nctrl * trk->ctrlpr);
	trk->env = realloc(trk->env, sizeof(envelope *) * trk->nctrl);

	pthread_mutex_unlock(&trk->exclctrl);
}

void track_swap_col(track *trk, int c, int c2) {
	if ((c > trk->ncols) || (c2 > trk->ncols)) {
		return;
	}

	module_excl_in();
	row *c3 = trk->rows[c];
	trk->rows[c] = trk->rows[c2];
	trk->rows[c2] = c3;
	module_excl_out();
}

void track_swap_ctrl(track *trk, int c, int c2) {
	if ((c > trk->nctrl) || (c2 > trk->nctrl)) {
		return;
	}

	// don't allow swapping with pitch (c == 0)
	if (c < 1 || c2 < 1) {
		return;
	}

	pthread_mutex_lock(&trk->exclctrl);

	int *cc3 = trk->ctrl[c];
	trk->ctrl[c] = trk->ctrl[c2];
	trk->ctrl[c2] = cc3;

	int c3 = trk->ctrlnum[c];
	trk->ctrlnum[c] = trk->ctrlnum[c2];
	trk->ctrlnum[c2] = c3;

	ctrlrow *cr3 = trk->crows[c];
	trk->crows[c] = trk->crows[c2];
	trk->crows[c2] = cr3;

	envelope *env3 = trk->env[c];
	trk->env[c] = trk->env[c2];
	trk->env[c2] = env3;

	pthread_mutex_unlock(&trk->exclctrl);
}

void track_resize(track *trk, int size) {
	module_excl_in();

	// no need to realloc?
	if (trk->arows >= size) {
		trk->nrows = size;
		trk->resync = 1;
		module_excl_out();
		return;
	}

	trk->arows = size * 2;

	pthread_mutex_lock(&trk->exclctrl);

	for (int c = 0; c < trk->ncols; c++) {
		trk->rows[c] = realloc(trk->rows[c], sizeof(row) * trk->arows);

		for (int n = trk->nrows; n < trk->arows; n++) {
			trk->rows[c][n].type = none;
			trk->rows[c][n].note = 0;
			trk->rows[c][n].velocity = 0;
			trk->rows[c][n].delay = 0;
		}
	}

	for (int c = 0; c < trk->nctrl; c++) {
		trk->ctrl[c] = realloc(trk->ctrl[c], sizeof(int) * trk->arows * trk->ctrlpr);
		trk->crows[c] = realloc(trk->crows[c], sizeof(ctrlrow) * trk->arows);
		for (int n = trk->nrows; n < trk->arows; n++) {
			trk->crows[c][n].velocity = -1;
			trk->crows[c][n].linked = 0;
			trk->crows[c][n].smooth = 0;
			trk->crows[c][n].anchor = 0;
		}

		envelope_resize(trk->env[c], trk->arows, trk->ctrlpr);
		for (int n = trk->nrows; n < trk->arows; n++) {
			for (int nn = 0; nn < trk->ctrlpr; nn++) {
				trk->ctrl[c][(n * trk->ctrlpr) + nn] = -1;
			}
		}
	}

	pthread_mutex_unlock(&trk->exclctrl);

	trk->nrows = size;

	module_excl_out();
	track_clear_updates(trk);
}

void track_trigger(track *trk) {
	if (trk->playing) {
		trk->playing = 0;
		track_kill_notes(trk);
	} else {
		trk->playing = 1;
	}
}

char *track_get_rec_update(track *trk) {
	static char rc[256];
	pthread_mutex_lock(&trk->exclrec);

	char *ret = NULL;

	if (trk->cur_rec_update > 0) {
		sprintf(rc, "{\"col\" :%d, \"row\" : %d}", trk->updates[trk->cur_rec_update - 1].col,
		        trk->updates[trk->cur_rec_update - 1].row);
		trk->cur_rec_update--;
		ret = rc;
	}

	pthread_mutex_unlock(&trk->exclrec);
	return ret;
}

void track_insert_rec_update(track *trk, int col, int row) {
	if (trk->cur_rec_update > 0) {
		if ((trk->updates[trk->cur_rec_update - 1].col == col)
		        && (trk->updates[trk->cur_rec_update - 1].row == row)) {
			return;
		}
	}

	pthread_mutex_lock(&trk->exclrec);

	trk->updates[trk->cur_rec_update].col = col;
	trk->updates[trk->cur_rec_update].row = row;
	trk->cur_rec_update++;

	pthread_mutex_unlock(&trk->exclrec);
}

void track_clear_updates(track *trk) {
	pthread_mutex_lock(&trk->exclrec);

	trk->cur_rec_update = 0;

	pthread_mutex_unlock(&trk->exclrec);
}

int col_has_note(track *trk, int col, int note) {
	int found_notes = 0;
	for (int y = 0; y < trk->nrows; y++) {
		if (trk->rows[col][y].type == note_on) {
			found_notes = 1;
			if (trk->rows[col][y].note == note)
				return 1;
		}
	}

	if (!found_notes)
		return 1;

	return 0;
}

// shit gets real
void track_handle_record(track *trk, midi_event evt) {
	double pos = trk->last_pos + ((trk->last_period / (double)jack_buffer_size) * evt.time);

	int p = floorf(pos);
	double rem = pos - p;

	if (rem >= .5) {
		p++;
		rem = -(1.0 - rem);
	}

	int t = floorf(50.0 * rem);

	if (p > trk->nrows - 1)
		p = p - trk->nrows;


	int c = 0;
	int found = 0;
	// are we in a sounding note? try next column
	if (trk->channel != 10) {
		if (evt.type == note_on) {
			for (int col = 0; col < trk->ncols && !found; col++) {
				c = col;
				int ln = col_last_note(trk, col, p);
				if (ln == -1 || ln == evt.note) {
					found = 1;
				}
			}

			if (!found) {
				track_add_col(trk);
				c = trk->ncols - 1;
			}
		}
	}

	// if drums, find a column with given note
	if (trk->channel == 10) {
		if (evt.type == note_on) {
			int found = 0;

			for (int col = 0; col < trk->ncols && found == 0; col++) {
				if (col_has_note(trk, col, evt.note)) {
					c = col;
					found = 1;
				}
			}

			if (!found) {
				track_add_col(trk);
				c = trk->ncols - 1;
			}
		}
	}

	// find the possibly wandering note_on
	if (evt.type == note_off) {
		int found = 0;

		for (int col = 0; col < trk->ncols; col++) {
			if (col_last_note(trk, col, p) == evt.note) {
				found = 1;
				c = col;

				int wanderer = track_get_wandering_note(trk, c, p);
				if (wanderer >-1) {
					track_set_wanderer(trk, c, wanderer, 0);
				}
			}
		}

		if (!found)
			return;
	}

	row r;
	track_get_row(trk, c, p, &r);

	// try not to overwrite note_ons with note_offs
	if (evt.type == note_off && r.type == note_on) {
		return;
	}

	if (p > trk->nrows - 1)
		p = p - trk->nrows;


	if (evt.type == note_on || evt.type == note_off) {
		track_set_row(trk, c, p, evt.type, evt.note, evt.velocity, t);
	}

	if (evt.type == note_on) {
		track_set_wanderer(trk, c, p, 1);
	}

	if (!(evt.type == pitch_wheel || evt.type == control_change))
		return;

	int ctrl = evt.control;

	int ctrlval = evt.msb;

	if (evt.type == pitch_wheel) {
		ctrl = -1;
		ctrlval = (ctrlval * 128) + evt.lsb;
	}

	int pp = (p * trk->ctrlpr) + (int)((pos - p) * trk->ctrlpr);

	/*char buff[256];
	printf("rec: %f %s -> %f : %d:%d %d:%d:%d\n", trk->pos, midi_describe_event(evt, buff, 256), pos, p, t, ctrl, pp, ctrlval);
	*/

	int nc = -1;

	for (int c = 0; c < trk->nctrl; c++) {
		if (trk->ctrlnum[c] == ctrl)
			nc = c;
	}

	if (nc == -1) {
		track_add_ctrl(trk, ctrl);
	}

	for (int c = 0; c < trk->nctrl; c++) {
		if (trk->ctrlnum[c] == ctrl) {
			nc = c;
			trk->lctrlval[c] = ctrlval;
		}
	}

	while (pp >= trk->ctrlpr * trk->nrows) {
		pp -= trk->ctrlpr * trk->nrows;
	}

	track_set_ctrl(trk, nc, pp, ctrlval);
}

int track_get_lctrlval(track *trk, int c) {
	int ret = -1;
	pthread_mutex_lock(&trk->exclctrl);
	ret = trk->lctrlval[c];
	pthread_mutex_unlock(&trk->exclctrl);
	return ret;
}
