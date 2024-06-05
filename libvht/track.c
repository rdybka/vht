/* track.c - vahatraker (libvht)
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

#include <Python.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <math.h>

#include "midi_client.h"
#include "module.h"
#include "track.h"
#include "row.h"

void trk_mod_excl_in(track *trk) {
	if (trk->mod_excl)
		pthread_mutex_lock(trk->mod_excl);
}

void trk_mod_excl_out(track *trk) {
	if (trk->mod_excl)
		pthread_mutex_unlock(trk->mod_excl);
}

void trk_should_save(track *trk) {
	if (trk->clt) {
		midi_client *clt = (midi_client *)trk->clt;
		module *mod = (module *)clt->mod_ref;
		mod->should_save = 1;
	}
}

track *track_new(int port, int channel, int len, int songlen, int ctrlpr) {
	track *trk = malloc(sizeof(track));
	if (len == -1)
		len = 32;

	if (songlen == -1)
		songlen = len;

	trk->channel = channel;
	trk->nrows = len;
	trk->arows = len;
	trk->nsrows = songlen;
	trk->index = 0;
	trk->loop = 1;
	trk->ncols = 1;
	trk->playing = 0;
	trk->port = port;
	trk->cur_rec_update = 0;
	trk->resync = 0;
	trk->prog_send = 0;
	trk->prog = -1;
	trk->prog_sent = 0;
	trk->bank_msb = -1;
	trk->bank_lsb = -1;
	trk->qc1_send = 0;
	trk->qc1_ctrl = -1;
	trk->qc1_val = -1;
	trk->qc1_last = -1;
	trk->qc2_send = 0;
	trk->qc2_ctrl = -1;
	trk->qc2_val = -1;
	trk->qc2_last = -1;
	trk->extras = NULL;
	trk->clt = NULL;

	pthread_mutex_init(&trk->excl, NULL);
	pthread_mutex_init(&trk->exclrec, NULL);
	pthread_mutex_init(&trk->exclctrl, NULL);
	trk->mod_excl = NULL;

	trk->rows = malloc(sizeof(row*) * trk->ncols);
	trk->ring = malloc(sizeof(int) * trk->ncols);
	trk->lplayed = malloc(sizeof(int) * trk->ncols);
	trk->lsounded = malloc(sizeof(int) * trk->ncols);
	trk->mand_qnt = malloc(sizeof(int) * trk->ncols);

	for (int c = 0; c < trk->ncols; c++) {
		trk->rows[c] = malloc(sizeof(row) * trk->nrows);
		track_clear_rows(trk, c);

		trk->ring[c] = -1;
		trk->lplayed[c] = -1;
		trk->lsounded[c] = -1;
		trk->mand_qnt[c] = -232323;
	}

	trk->ctrlpr = ctrlpr;
	if (trk->ctrlpr < 1)
		trk->ctrlpr = TRACK_DEF_CTRLPR;
	trk->nctrl = 0;
	trk->ctrl = 0;
	trk->ctrlnum = 0;
	trk->lctrlval = 0;
	trk->lctrlrow = 0;
	trk->env = 0;

	trk->crows = 0;

	trk->playing = 1;
	trk->indicators = 0;
	trk->dirty = 0;
	trk->dirty_wheel = 0;

	track_add_ctrl(trk, -1);

	trk->mand = mandy_new(trk);
	track_reset(trk);
	return trk;
};

void track_reset(track *trk) {
	trk->pos = trk->last_pos = trk->last_period = 0.0;
	trk->prog_sent = 0;
	trk->qc1_last = -1;
	trk->qc2_last = -1;
	trk->loop = 1;
	for (int c = 0; c < trk->ncols; c++) {
		trk->lplayed[c] = -1;
		trk->lsounded[c] = -1;
		trk->mand_qnt[c] = -232323;
	}

	for (int c = 0; c < trk->nctrl; c++) {
		trk->lctrlrow[c] = -1;
		trk->lctrlval[c] = -1;
	}

	if (trk->mand->active) {
		mandy_reset(trk->mand);
	}

	for (int c = 0; c < trk->ncols; c++) {
		for (int r = 0; r < trk->nrows; r++) {
			row_randomise(&trk->rows[c][r]);
			trk->rows[c][r].clt = trk->clt;
		}
	}
}

// this is used whiled recording
void track_set_row(track *trk, int c, int n, int type, int note, int velocity, int delay) {
	pthread_mutex_lock(&trk->excl);

	row *r = &trk->rows[c][n];
	r->type = type;
	r->note = note;
	r->velocity = velocity;
	r->delay = delay;
	r->ringing = 0;
	r->prob = 0;
	r->velocity_range = 0;
	r->velocity_next = velocity;
	r->delay_range = 0;
	r->delay_next = delay;

	for (int c = 0; c < trk->nctrl; c++)
		trk->lctrlval[c] = -1;

	pthread_mutex_unlock(&trk->excl);
	track_insert_rec_update(trk, c, n);
	trk->dirty = 1;
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
	r->prob = s->prob;
	r->delay_range = s->delay_range;
	r->delay_next = s->delay_next;
	r->velocity_range = s->velocity_range;
	r->velocity_next = s->velocity_next;
	r->clt = trk->clt;
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
	trk_should_save(trk);
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
	trk_should_save(trk);
	pthread_mutex_unlock(&trk->exclctrl);
}

int track_get_indicators(track *trk) {
	trk->indicators &= ~8;
	for (int c = 0; c < trk->ncols; c++) {
		if (trk->ring[c] > -1)
			trk->indicators |= 8;
	}

	return trk->indicators;
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

char *track_get_extras(track *trk) {
	return trk->extras;
}

void track_set_extras(track *trk, char *extr) {
	trk_should_save(trk);
	//printf("xtra: %p <- %s\n", trk, extr);
	if (extr == NULL) {
		free(trk->extras);
		trk->extras = NULL;
		return;
	}

	free(trk->extras);
	int l = strlen(extr);
	trk->extras = malloc(l + 1);
	strcpy(trk->extras, extr);
}


void track_free(track *trk) {
	track_kill_notes(trk);

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

	free(trk->extras);
	free(trk->crows);
	free(trk->ring);
	free(trk->lplayed);
	free(trk->lsounded);
	free(trk->rows);
	free(trk->ctrl);
	free(trk->ctrlnum);
	free(trk->lctrlval);
	free(trk->lctrlrow);
	free(trk->env);
	mandy_free(trk->mand);
	free(trk->mand_qnt);
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
		trk->rows[c][t].prob = 0;
		trk->rows[c][t].velocity_range = 0;
		trk->rows[c][t].delay_range = 0;
		trk->rows[c][t].velocity_next = 100;
		trk->rows[c][t].delay_next = 0;
		trk->rows[c][t].clt = trk->clt;
	}

	pthread_mutex_unlock(&trk->excl);
}

void track_clear_crows(track *trk, int c) {
	pthread_mutex_lock(&trk->exclctrl);

	for (int t = 0; t < trk->nrows; t++) {
		trk->crows[c][t].velocity = -1;
		trk->crows[c][t].linked = 0;
		trk->crows[c][t].smooth = 0;
		trk->crows[c][t].anchor = 0;
	}

	pthread_mutex_unlock(&trk->exclctrl);
}

void track_clear_ctrl(track *trk, int c) {
	pthread_mutex_lock(&trk->exclctrl);

	for (int t = 0; t < trk->nrows; t++) {
		trk->crows[c][t].velocity = -1;
		trk->crows[c][t].linked = 0;
		trk->crows[c][t].smooth = 0;
		trk->crows[c][t].anchor = 0;
	}

	for (int r = 0; r < trk->nrows * trk->ctrlpr; r++) {
		trk->ctrl[c][r] = -1;
	}

	pthread_mutex_unlock(&trk->exclctrl);
}


track *track_clone(track *src) {
	track *dst = track_new(src->port, src->channel, src->nrows, src->nsrows, src->ctrlpr);

	for (int c = 0; c < src->ncols; c++) {
		if (c > 0)
			track_add_col(dst);

		for (int r = 0; r < src->nrows; r++) {
			row *s = &src->rows[c][r];
			row_set(&dst->rows[c][r], s->type, s->note, s->velocity, s->delay, s->prob, s->velocity_range, s->delay_range);
			dst->rows[c][r].prob = s->prob;
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

		dst->prog = src->prog;
		dst->prog_sent = src->prog_sent;

		dst->bank_msb = src->bank_msb;
		dst->bank_lsb = src->bank_lsb;
		dst->qc1_ctrl = src->qc1_ctrl;
		dst->qc1_last = src->qc1_last;
		dst->qc1_val = src->qc1_val;
		dst->qc2_ctrl = src->qc2_ctrl;
		dst->qc2_last = src->qc2_last;
		dst->qc2_val = src->qc2_val;
		dst->loop = src->loop;
		dst->pos = src->pos;
		dst->last_pos = src->last_pos;
		dst->last_period = src->last_period;
		dst->indicators = src->indicators;
		dst->playing = src->playing;
		dst->resync = 1;
		mandy_clone(src->mand, dst);
		track_set_extras(dst, src->extras);
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
	if (col >= trk->ncols)
		return -1;

	if (trk->rows[col][(int)pos].type == note_on) {
		return trk->rows[col][(int)pos].note;
	}

	if (trk->rows[col][(int)pos].type == note_off) {
		return -1;
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

void trk_mod_panic(module *mod, int prt) {
	for (int s = 0; s < mod->nseq; s++) {
		for (int t = 0; t < mod->seq[s]->ntrk; t++) {
			if (mod->seq[s]->trk[t]->port == prt) {
				track_kill_notes(mod->seq[s]->trk[t]);
				mod->seq[s]->thumb_panic = 9;
				queue_midi_ctrl(mod->clt, mod->seq[s], mod->seq[s]->trk[t], 0, 0x7B);
			}
		}
	}

	for (int s = 0; s < mod->tline->nstrips; s++) {
		for (int t = 0; t < mod->tline->strips[s].seq->ntrk; t++) {
			if (mod->seq[s]->trk[t]->port == prt) {
				track_kill_notes(mod->tline->strips[s].seq->trk[t]);
				mod->tline->strips[s].seq->thumb_panic = 9;
			}
		}
	}

	mod->panic = 1;
}

// yooohoooo!!!
void track_play_row(track *trk, int pos, int c, int delay) {
	row r;

	if (trk->lplayed[c] == pos && !trk->mand->active) {
		return;
	}

	track_get_row(trk, c, pos, &r);
	trk->lplayed[c] = pos;

	if (r.type == none)
		return;

	if (r.prob > 0) {
		int rnd = rand() % 100;

		if (r.prob > 100) {
			trk->rows[c][pos].prob = 0; // ugly #hack
			r.prob = 0;
		}

		if (rnd < r.prob) {
			row_randomise(&trk->rows[c][pos]);
			return;
		}
	}

	midi_client *clt = (midi_client *)trk->clt;
	module *mod = (module *)clt->mod_ref;

	midi_event evt;

	if (r.type == note_on || r.type == note_off ) {
		if (mod->pnq_hack && trk->channel == 16 && r.note == 127) {
			trk_mod_panic(mod, trk->port);
			trk->indicators |= 4;
			trk->ring[c] = 127;
			trk->lsounded[c] = -1;
			return;
		}

		if (mod->pnq_hack && trk->channel == 16 && r.type == note_off && trk->ring[c] == 127) {
			trk->indicators |= 4;
			trk->ring[c] = -1;
			trk->lsounded[c] = -1;
			mod->panic = 0;
			return;
		}

		if (trk->ring[c] != -1) {
			evt.time = delay;
			evt.channel = trk->channel;
			evt.type = note_off;
			evt.note = trk->ring[c];
			evt.velocity = 64;
			midi_buffer_add(trk->clt, trk->port, evt);
			module_handle_inception(trk, evt);
			trk->indicators |= 4;
			trk->ring[c] = -1;
			trk->lsounded[c] = -1;
		}
	}

	if (r.type != note_off) {
		evt.time = delay;
		evt.channel = trk->channel;
		evt.type = r.type;
		evt.note = r.note;
		evt.velocity = r.velocity_next;
		trk->lsounded[c] = pos;

		midi_buffer_add(trk->clt, trk->port, evt);
		module_handle_inception(trk, evt);

		row_randomise(&trk->rows[c][pos]);

		// fix wandering notes?
		if (!mod->recording) {
			if (r.type == note_on)
				trk->ring[c] = r.note;
			return;
		}

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

	if (r.type == note_on && !trk->mand->active) {
		trk->ring[c] = r.note;
		track_set_wanderer(trk, c, pos, 0);
	}
}

void track_fix_program_change(track *trk) {
	// send program change?
	if (trk->prog > -1) {
		midi_client *clt = (midi_client *)trk->clt;

		if ((trk->prog_sent == 0))  {
			int send_last = 0;

			trk->prog_sent = 1;
			midi_event evt;

			evt.time = 1;
			evt.channel = trk->channel;
			evt.type = control_change;
			evt.control = 0;
			evt.data = trk->bank_msb;

			if (trk->bank_msb > -1) {
				midi_buffer_add(clt, trk->port, evt);
				send_last = 1;
			}

			evt.time = 2;
			evt.channel = trk->channel;
			evt.type = control_change;
			evt.control = 32;
			evt.data = trk->bank_lsb;

			if (trk->bank_lsb > -1) {
				midi_buffer_add(clt, trk->port, evt);
				send_last = 1;
			}

			evt.time = 0;
			if (send_last) {
				evt.time = 3;
			}

			evt.channel = trk->channel;
			evt.type = program_change;
			evt.control = trk->prog;
			evt.data = 0;

			midi_buffer_add(clt, trk->port, evt);

			trk->indicators |= 8;
		}
	}
}

int get_ctrl_v(track *trk, int c, int r) {
	int ret = -1;
	int nc = trk->nrows * trk->ctrlpr;

	if (r < 0)
		r += nc;

	if (r >= nc)
		r -= nc;

	ret = env_get_v(trk->env[c], trk->ctrlpr, (float)r / (float)trk->ctrlpr);
	if (ret > -1 && c == 0) {
		ret *= 128;
	}

	if (ret == -1)
		ret = trk->ctrl[c][r];

	return ret;
}

void track_strum(track *trk, double pos_from, double pos_to, jack_nframes_t nframes) {
	if (!trk->playing)
		return;

	int rw0 = (int)pos_to;
	rw0 -= 1;

	int strum_down = 1;
	if (pos_to < pos_from) {
		strum_down = 0;
	}

	midi_client *clt = (midi_client *)trk->clt;

	// sound notes
	for (int c = 0; c < trk->ncols; c++) {
		int strummed = 0;
		for (int rw = rw0; rw < rw0 + 3 && !strummed; rw++) {
			row r;
			int rrw = rw;
			if (rrw < 0)
				rrw = 0;

			while (rrw >= trk->nrows)
				rrw -= trk->nrows;

			track_get_row(trk, c, rrw, &r);
			if(r.type == note_on || r.type == note_off) {
				double trigger_time = (double)rrw + ((double)r.delay / 100);
				unsigned int frm = fabs(round((trigger_time - trk->last_pos) / (pos_to - pos_from) * nframes));

				int play = 0;

				if (strum_down && trigger_time <= pos_to) {
					if (trigger_time > pos_from)
						play = 1;
				}

				if (!strum_down && trigger_time >= pos_to) {
					if (trigger_time < pos_from)
						play = 1;
				}

				if (pos_from > trk->nrows - 1 && pos_to < 1) {
					frm = fabs(round((trigger_time - (trk->last_pos - trk->nrows)) / (pos_to - (pos_from - trk->nrows)) * nframes));
					play = 1;
				} else if (pos_to > trk->nrows - 1 && pos_from < 1) {
					frm = fabs(round(((trk->last_pos - trigger_time) / (-((pos_to - trk->nrows) - pos_from))) * nframes));
					play = 1;
				}

				if (play && frm <= nframes) {
					if (trk->mand->tracies[0]->qnt == 0) {
						track_play_row(trk, rrw, c, (clt->jack_buffer_size - nframes) + frm);
					} else {
						trk->mand_qnt[c] = -(++rrw);
					}
					//printf("strum: %f -> %f %d -- %d:%d:%.3f:%d\n", trk->last_pos, trk->pos, strum_down, c, rrw, trigger_time, frm);
					strummed = 1;
				}
			}
		}
	}

	// controllers
	for (int c = 0; c < trk->nctrl; c++) {
		int ctrlto = (pos_to  / trk->nrows) * trk->nrows * trk->ctrlpr;
		int ctrlfrom = (pos_from  / trk->nrows) * trk->nrows * trk->ctrlpr;
		int ctrl = trk->ctrlnum[c];
		int found = 0;
		int data = -1;
		int nc = trk->nrows * trk->ctrlpr;
		int drow = 0;

		if (abs(ctrlto - ctrlfrom) > trk->nrows / 2) {
			if (strum_down) {
				ctrlto -= nc;
			} else {
				ctrlto += nc;
			}

			strum_down = !strum_down;
		}

		if (strum_down) {
			for (int r = ctrlto; r >= ctrlfrom && !found; r--) {
				data = get_ctrl_v(trk, c, r);
				if (data > -1) {
					found = 1;
					drow = r;
				}
			}
		} else {
			for (int r = ctrlto; r <= ctrlfrom && !found; r++) {
				data = get_ctrl_v(trk, c, r);
				if (data > -1) {
					found = 1;
					drow = r;
				}
			}
		}

		if (drow < 0)
			drow += nc;

		if (drow >= nc)
			drow -= nc;

		if (data > -1) {
			midi_event evt;

			evt.time = 0;
			evt.channel = trk->channel;
			evt.type = control_change;
			evt.control = ctrl;
			evt.data = data;

			if (ctrl == -1) {
				evt.type = pitch_wheel;
				evt.msb = data / 128;
				evt.lsb = data - (evt.msb * 128);

				if (evt.msb == 64 && evt.lsb == 0) {
					trk->dirty_wheel = 0;
				} else {
					trk->dirty_wheel = 1;
				}
			}

			if (data != trk->lctrlval[c] || drow != trk->lctrlrow[c]) {
				trk->lctrlval[c] = data;
				trk->lctrlrow[c] = drow;
				midi_buffer_add(clt, trk->port, evt);
				module_handle_inception(trk, evt);
				trk->indicators |= 4;
			}
		}
	}
}

void track_advance(track *trk, double speriod, jack_nframes_t nframes) {
	if (trk->resync) {
		return;
	}

	midi_client *clt = (midi_client *)trk->clt;

	// length of period in track time
	double tperiod = ((double)trk->nrows / (double)trk->nsrows) * speriod;
	double tmul = (double) nframes / tperiod;

	int row_start = floorf(trk->pos);
	if (row_start == trk->nrows) {
		row_start = 0;
	}

	int row_end = floorf(trk->pos + tperiod) + 1;
	if (row_end > trk->nrows)
		row_end = trk->nrows;

	if (trk->prog_sent == -1) {
		trk->prog_sent = 0;
		track_fix_program_change(trk);
	}

	if (trk->prog_send)
		track_fix_program_change(trk);

	// quick controls
	if (trk->pos < trk->last_pos || trk->last_pos == 0.0 ||\
	        trk->qc1_last != trk->qc1_val || trk->qc2_last != trk->qc2_val) {
		midi_event evt;

		evt.time = 0;
		evt.channel = trk->channel;
		evt.type = control_change;

		if (trk->qc1_ctrl > 0 && trk->qc1_send) {
			if (trk->qc1_val != trk->qc1_last) {
				evt.control = trk->qc1_ctrl;
				evt.data = trk->qc1_val;
				midi_buffer_add(clt, trk->port, evt);
				trk->indicators |= 4;
				trk->qc1_last = trk->qc1_val;
			}
		}

		if (trk->qc2_ctrl > 0  && trk->qc2_send) {
			if (trk->qc2_val != trk->qc2_last) {
				evt.control = trk->qc2_ctrl;
				evt.data = trk->qc2_val;
				midi_buffer_add(clt, trk->port, evt);
				trk->indicators |= 4;
				trk->qc2_last = trk->qc2_val;
			}
		}
	}

	if (trk->mand->active) {
		mandy_advance(trk->mand, tperiod, nframes);

		if (trk->playing) {
			track_strum(trk, trk->last_pos, trk->pos, nframes);

			for (int c = 0; c < trk->ncols; c++) {
				int qnt = trk->mand_qnt[c];
				if (qnt > -1) {
					track_play_row(trk, qnt, c, clt->jack_buffer_size - nframes);
					trk->mand_qnt[c] = -232323;
				}
			}
		}

		trk->last_pos = trk->pos;
		trk->last_period = tperiod;
		return;
	}

	// play notes
	//if (!(!row_start && row_end == trk->nrows))
	for (int c = 0; c < trk->ncols; c++)
		for (int n = row_start; n <= row_end; n++) {
			int nn = n;

			if (nn >= trk->nrows) {
				nn = 0;

				if (!trk->loop) {
					return;
				}
			}

			if (nn < trk->nrows) {
				row r;
				track_get_row(trk, c, nn, &r);

				double trigger_time = (double)n + ((double)r.delay_next / 100);
				double delay = trigger_time - trk->pos;
				double fdelay = (clt->jack_buffer_size - nframes) + delay * tmul;
				unsigned int frm = fabs(round(fdelay));

				if (frm == 0 && fdelay < 0.0)
					fdelay = 0.0;

				// infinity
				if (fdelay > 23 * clt->jack_buffer_size) {
					fdelay = 7 * clt->jack_buffer_size;
					frm = 2323;
				}

				if (fdelay >= 0.0 && frm < clt->jack_buffer_size) {
					if (trk->playing) {
						track_play_row(trk, nn, c, frm);
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

			while(rr >= trk->nrows * trk->ctrlpr) {
				trk->lctrlrow[c] = -1;
				trk->lctrlval[c] = -1;
				rr -= trk->nrows * trk->ctrlpr;
			}

			double delay = ((double)r / trk->ctrlpr) - trk->pos;

			int ctrl = trk->ctrlnum[c];

			float dt = env_get_v(trk->env[c],  trk->ctrlpr, (float)rr / (float)trk->ctrlpr);
			int data = dt;

			if ((data > -1) && (c == 0)) { // pitchwheel
				data = dt * 128;
			}

			if (data == -1) {
				data = trk->ctrl[c][rr];
			}

			if (data > -1) {
				midi_event evt;

				evt.time = (clt->jack_buffer_size - nframes) + delay * tmul;
				evt.channel = trk->channel;
				evt.type = control_change;
				evt.control = ctrl;
				evt.data = data;

				if (ctrl == -1) {
					evt.type = pitch_wheel;
					evt.msb = data / 128;
					evt.lsb = data - (evt.msb * 128);

					if (evt.msb == 64 && evt.lsb == 0) {
						trk->dirty_wheel = 0;
					} else {
						trk->dirty_wheel = 1;
					}
				}

				if ((delay >= 0) && (delay < tperiod)) {
					if (trk->playing) {
						if (data != trk->lctrlval[c] || rr != trk->lctrlrow[c]) {
							trk->lctrlval[c] = data;
							trk->lctrlrow[c] = rr;
							module_handle_inception(trk, evt);
							midi_buffer_add(clt, trk->port, evt);
							trk->indicators |= 4;
						}
					}
				}
			}

			delay += cper;
		}
	}

	trk->last_pos = trk->pos;
	trk->last_period = tperiod;

	if (!(trk->mand && trk->mand->active))
		trk->pos += tperiod;

	if (trk->loop) {
		if (trk->pos > trk->nrows) {
			trk->pos -= trk->nrows;
		}
		trk->last_pos = trk->pos - tperiod;
	}

	// update midi_out ind if ringing
	for (int c = 0; c < trk->ncols; c++)
		if (trk->ring[c] != -1)
			trk->indicators |= 4;
}

void track_wind(track *trk, double period) {
	double tperiod = ((double)trk->nrows / (double)trk->nsrows) * period;
	trk->last_pos = trk->pos;
	trk->pos += tperiod;
	while (trk->pos > trk->nsrows)
		trk->pos -= trk->nsrows;
}

void track_kill_notes(track *trk) {
	pthread_mutex_lock(&trk->excl);

	midi_client *clt = (midi_client *)trk->clt;
	if (!clt) {
		pthread_mutex_unlock(&trk->excl);
		return;
	}

	module *mod = (module *)clt->mod_ref;

	midi_event evtp;
	evtp.type = pitch_wheel;
	evtp.channel = trk->channel;
	evtp.note = 0;
	evtp.velocity = 64;
	evtp.time = clt->jack_buffer_size;

	if (trk->dirty_wheel) {
		midi_buffer_add(trk->clt, trk->port, evtp);
		trk->dirty_wheel = 0;
	}

	for (int c = 0; c < trk->ncols; c++) {
		if (trk->ring[c] != -1) {
			if (mod->pnq_hack && trk->ring[c] == 127) {
				mod->panic = 0;
			}

			midi_event evt;

			evt.type = note_off;
			evt.channel = trk->channel;
			evt.note = trk->ring[c];
			evt.velocity = 0;
			evt.time = clt->jack_buffer_size;

			if (trk->clt) {
				midi_buffer_add(trk->clt, trk->port, evt);
			}

			trk->ring[c] = -1;
		}

		trk->lplayed[c] = -1;
		trk->lsounded[c] = -1;
		trk->mand_qnt[c] = -232323;

		for (int t = 0; t < trk->nrows; t++) {
			trk->rows[c][t].ringing = 0;
		}
	}

	for (int c = 0; c < trk->nctrl; c++) {
		trk->lctrlrow[c] = -1;
		trk->lctrlval[c] = -1;
	}

	trk->indicators = 0;

	pthread_mutex_unlock(&trk->excl);
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
	trk->lplayed = realloc(trk->lplayed, sizeof(int) * trk->ncols);
	trk->lsounded = realloc(trk->lsounded, sizeof(int) * trk->ncols);
	trk->mand_qnt = realloc(trk->mand_qnt, sizeof(int) * trk->ncols);

	trk->ring[trk->ncols - 1] = -1;
	trk->lplayed[trk->ncols - 1] = -1;
	trk->lsounded[trk->ncols - 1] = -1;
	trk->mand_qnt[trk->ncols - 1] = -1;
	trk->dirty = 1;
	trk_should_save(trk);
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
	trk->lctrlrow = realloc(trk->lctrlrow, sizeof(int) * trk->nctrl);

	if (c == 0) {
		trk->lctrlval[trk->nctrl -1] = 64 * 127;
	} else {
		trk->lctrlval[trk->nctrl -1] = -1;
		trk->lctrlrow[trk->nctrl -1] = -1;
	}
	trk->env = realloc(trk->env, sizeof(envelope *) * trk->nctrl);
	trk->env[trk->nctrl -1] = envelope_new(trk->nrows, trk->ctrlpr);

	trk->crows = realloc(trk->crows, sizeof(ctrlrow *) * trk->nctrl);
	trk->crows[trk->nctrl - 1] = malloc(sizeof(ctrlrow) * trk->arows);

	for (int r = 0; r < trk->ctrlpr * trk->arows; r++) {
		trk->ctrl[trk->nctrl -1][r] = -1;
	}
	trk_should_save(trk);
	pthread_mutex_unlock(&trk->exclctrl);

	track_clear_crows(trk, trk->nctrl - 1);
}

void track_del_col(track *trk, int c) {
	if ((c >= trk->ncols) || (c < 0) || (trk->ncols == 1)) {
		return;
	}

	trk_mod_excl_in(trk);

	for (int cc = c; cc < trk->ncols - 1; cc++) {
		trk->rows[cc] = trk->rows[cc+1];
		trk->ring[cc] = trk->ring[cc+1];
		trk->lplayed[cc] = trk->lplayed[cc+1];
		trk->lsounded[cc] = trk->lsounded[cc+1];
		trk->mand_qnt[cc] = trk->mand_qnt[cc+1];
	}

	trk->ncols--;

	trk->rows = realloc(trk->rows, sizeof(row*) * trk->ncols);
	trk->ring = realloc(trk->ring, sizeof(int) * trk->ncols);
	trk->lplayed = realloc(trk->lplayed, sizeof(int) * trk->ncols);
	trk->lsounded = realloc(trk->lsounded, sizeof(int) * trk->ncols);
	trk->mand_qnt = realloc(trk->mand_qnt, sizeof(int) * trk->ncols);

	trk->dirty = 1;
	trk_should_save(trk);
	trk_mod_excl_out(trk);
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
	trk->lctrlval = realloc(trk->lctrlval, sizeof(int) * trk->nctrl);
	trk->lctrlrow = realloc(trk->lctrlrow, sizeof(int) * trk->nctrl);
	trk_should_save(trk);
	pthread_mutex_unlock(&trk->exclctrl);
}

void track_swap_col(track *trk, int c, int c2) {
	if ((c > trk->ncols) || (c2 > trk->ncols)) {
		return;
	}

	trk_mod_excl_in(trk);
	row *c3 = trk->rows[c];
	trk->rows[c] = trk->rows[c2];
	trk->rows[c2] = c3;
	trk->dirty = 1;
	trk_mod_excl_out(trk);
	trk_should_save(trk);
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

	int lc = trk->lctrlval[c];
	trk->lctrlval[c] = trk->lctrlval[c2];
	trk->lctrlval[c2] = lc;

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
	trk_should_save(trk);
}

void track_clear_updates(track *trk) {
	pthread_mutex_lock(&trk->exclrec);

	trk->cur_rec_update = 0;

	pthread_mutex_unlock(&trk->exclrec);
}

void track_resize(track *trk, int size) {
	pthread_mutex_lock(&trk->excl);

	trk->arows = size * 2;

	pthread_mutex_lock(&trk->exclctrl);

	for (int c = 0; c < trk->ncols; c++) {
		trk->rows[c] = realloc(trk->rows[c], sizeof(row) * trk->arows);

		for (int n = trk->nrows; n < trk->arows; n++) {
			trk->rows[c][n].type = none;
			trk->rows[c][n].note = 0;
			trk->rows[c][n].velocity = 0;
			trk->rows[c][n].delay = 0;
			trk->rows[c][n].clt = trk->clt;
		}
	}

	for (int c = 0; c < trk->nctrl; c++) {
		trk->ctrl[c] = realloc(trk->ctrl[c], sizeof(int) * trk->arows * trk->ctrlpr);
		trk->crows[c] = realloc(trk->crows[c], sizeof(ctrlrow) * trk->arows);
		for (int n = trk->nrows - 1; n < trk->arows; n++) {
			trk->crows[c][n].velocity = -1;
			trk->crows[c][n].linked = 0;
			trk->crows[c][n].smooth = 0;
			trk->crows[c][n].anchor = 0;
		}

		for (int n = trk->nrows - 1; n < trk->arows; n++) {
			for (int nn = 0; nn < trk->ctrlpr; nn++) {
				trk->ctrl[c][(n * trk->ctrlpr) + nn] = -1;
			}
		}

		envelope_resize(trk->env[c], size, trk->ctrlpr);
		track_ctrl_refresh_envelope(trk, c);
	}

	pthread_mutex_unlock(&trk->exclctrl);

	trk->nrows = size;

	pthread_mutex_unlock(&trk->excl);
	track_clear_updates(trk);
	trk_should_save(trk);
	trk->dirty = 1;
}

void track_set_nrows(track *trk, int n) {
	track_resize(trk, n);
	trk->resync = 1;
	trk->dirty = 1;
}

void track_set_nsrows(track *trk, int n) {
	trk->nsrows = n;
	if (n > trk->nrows) {
		int nrows = trk->nrows;
		track_resize(trk, n);
		trk->nrows = nrows;
	}

	trk->resync = 1;
	trk->dirty = 1;
	trk_should_save(trk);
}

void track_double(track *trk) {
	int offs = trk->nrows;
	trk->nsrows *= 2;
	track_resize(trk, trk->nrows * 2);

	trk_mod_excl_in(trk);

	for (int c = 0; c < trk->ncols; c++) {
		for (int r = 0; r < offs; r++) {
			row *s = &trk->rows[c][r];
			trk->rows[c][r + offs].clt = trk->clt;
			row_set(&trk->rows[c][r + offs], s->type, s->note, s->velocity, s->delay, s->prob, s->velocity_range, s->delay_range);
		}
	}

	for (int c = 0; c < trk->nctrl; c++) {
		for (int r = 0; r < offs; r++) {
			ctrlrow *s = &trk->crows[c][r];
			ctrlrow_set(&trk->crows[c][r + offs], s->velocity, s->linked, s->smooth, s->anchor);

			for (int rr = 0; rr < trk->ctrlpr; rr++) {
				trk->ctrl[c][((r + offs) * trk->ctrlpr) + rr] = trk->ctrl[c][(r * trk->ctrlpr) + rr];
			}
		}

		track_ctrl_refresh_envelope(trk, c);
	}
	trk_should_save(trk);
	trk_mod_excl_out(trk);
}

void track_halve(track *trk) {
	int offs = trk->nrows / 2;
	for (int c = 0; c < trk->nctrl; c++) {
		for (int r = offs; r < trk->nrows; r++) {
			ctrlrow_set(&trk->crows[c][r], -1, 0, 0, 0);

			for (int rr = 0; rr < trk->ctrlpr; rr++) {
				trk->ctrl[c][(r * trk->ctrlpr) + rr] = -1;
			}
		}

		track_ctrl_refresh_envelope(trk, c);
	}

	track_resize(trk, trk->nrows / 2);
	trk->nsrows /= 2;
	trk_should_save(trk);
}

void track_trigger(track *trk) {
	if (trk->playing) {
		trk->playing = 0;
		track_kill_notes(trk);
	} else {
		trk->playing = 1;
	}
}

PyObject *track_get_rec_update(track *trk) {
	PyObject *ret = PyDict_New();

	pthread_mutex_lock(&trk->exclrec);

	if (trk->cur_rec_update > 0) {
		PyDict_SetItemString(ret, "col", PyLong_FromLong(trk->updates[trk->cur_rec_update - 1].col));
		PyDict_SetItemString(ret, "row", PyLong_FromLong(trk->updates[trk->cur_rec_update - 1].row));
		trk->cur_rec_update--;
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

	if (trk->clt) {
		midi_client *clt = (midi_client *)trk->clt;
		module *mod = (module *)clt->mod_ref;
		mod->should_save = 1;
	}

	pthread_mutex_lock(&trk->exclrec);

	trk->updates[trk->cur_rec_update].col = col;
	trk->updates[trk->cur_rec_update].row = row;
	trk->cur_rec_update++;

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
	midi_client *clt = (midi_client *)trk->clt;
	double pos = trk->last_pos + ((trk->last_period / (double)clt->jack_buffer_size) * evt.time);

	int p = floorf(pos);
	double rem = pos - p;

	trk->indicators |= 2;

	if (rem >= .5) {
		p++;
		rem = -(1.0 - rem);
	}

	int t = floorf(100.0 * rem);

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

		if (!found) {
			return;
		}
	}

	row r;
	track_get_row(trk, c, p, &r);

	// try not to overwrite note_ons with note_offs
	int cnt = trk->nrows;
	while (evt.type == note_off && r.type == note_on) {
		t = -49;
		p++;
		if (p >= trk->nrows)
			p = 0;

		track_get_row(trk, c, p, &r);
		cnt--;
		if (cnt < 0)
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

int track_get_last_row_played(track *trk, int col) {
	return trk->lsounded[col];
}

// from python, we will access envelopes through track
// all controllers will have envs added automatically
void track_envelope_add_node(track *trk, int c, float x, float y, float z, int linked) {
	envelope_add_node(trk->env[c], x, y, z, linked);
	trk_should_save(trk);
}

void track_envelope_del_node(track *trk, int c, int n) {
	envelope_del_node(trk->env[c], n);
	trk_should_save(trk);
}

void track_envelope_set_node(track *trk, int c, int n, float x, float y, float z, int linked) {
	envelope_set_node(trk->env[c], n, x, y, z, linked);
	trk_should_save(trk);
}

PyObject *track_get_envelope(track *trk, int c) {
	PyObject *ret = PyList_New(0);

	for (int n = 0; n < trk->env[c]->nnodes; n++) {
		PyObject *r = PyDict_New();

		PyDict_SetItemString(r, "x", PyFloat_FromDouble(trk->env[c]->nodes[n].x));
		PyDict_SetItemString(r, "y", PyFloat_FromDouble(trk->env[c]->nodes[n].y));
		PyDict_SetItemString(r, "z", PyFloat_FromDouble(trk->env[c]->nodes[n].z));
		PyDict_SetItemString(r, "l", PyLong_FromLong(trk->env[c]->nodes[n].linked));

		PyList_Append(ret, r);
	}

	return ret;
}

void track_swap_rows(track *trk, int rw1, int rw2) {
	for (int c = 0; c < trk->ncols; c++) {
		row curr_rw = trk->rows[c][rw2];
		trk->rows[c][rw2] = trk->rows[c][rw1];
		trk->rows[c][rw1] = curr_rw;
	}

	int *curr_dood = malloc(sizeof(int) * trk->ctrlpr);
	for (int c = 0; c < trk->nctrl; c++) {
		ctrlrow curr = trk->crows[c][rw2];
		trk->crows[c][rw2] = trk->crows[c][rw1];
		trk->crows[c][rw1] = curr;

		int ll = 0;
		for (int nn = rw2 * trk->ctrlpr ; nn < (rw2 + 1) * trk->ctrlpr; nn++) {
			curr_dood[ll++] = trk->ctrl[c][nn];
		}

		ll = 0;
		int nn2 = rw1 * trk->ctrlpr;
		for (int nn = rw2 * trk->ctrlpr ; nn < (rw2 + 1) * trk->ctrlpr; nn++) {
			trk->ctrl[c][nn] = trk->ctrl[c][nn2 + ll++];
		}

		ll = 0;
		for (int nn = rw1 * trk->ctrlpr ; nn < (rw1 + 1) * trk->ctrlpr; nn++) {
			trk->ctrl[c][nn] = curr_dood[ll++];
		}
	}
	free(curr_dood);
}

mandy *track_get_mandy(track *trk) {
	return trk->mand;
}


