/* track.h - vahatraker (libvht)
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

#ifndef __TRACK_H__
#define __TRACK_H__

#include <pthread.h>
#include "midi_event.h"
#include "row.h"
#include "ctrlrow.h"
#include "envelope.h"
#include "mandy.h"

#define TRACK_DEF_CTRLPR 16

typedef struct rec_update_t {
	int col;
	int row;
} rec_upd;

typedef struct track_t {
	int port;
	int channel;
	int nrows; // actual rows
	int nsrows; // song rows
	int playing;
	double pos;
	int index;

	// used for recording and mandy
	double last_pos;
	double last_period;

	int ncols;
	row **rows;
	envelope **env;

	int ctrlpr;
	int nctrl;
	int *ctrlnum;
	int *lctrlval;
	int *lctrlrow;
	int **ctrl;

	int prog_send;
	int prog;
	int prog_sent;
	int bank_msb;
	int bank_lsb;

	int qc1_send;
	int qc1_ctrl;
	int qc1_val;
	int qc1_last;

	int qc2_send;
	int qc2_ctrl;
	int qc2_val;
	int qc2_last;

	ctrlrow **crows;

	int arows; // allocated rows
	int *ring;
	int *lplayed;
	int *lsounded;
	int *mand_qnt;

	int resync;

	rec_upd updates[MIDI_EVT_BUFFER_LENGTH];
	int cur_rec_update;

	int loop;

	pthread_mutex_t excl; // for atomic row access - never used :)
	pthread_mutex_t exclrec; // for row changes
	pthread_mutex_t exclctrl; // for ctrls
	pthread_mutex_t *mod_excl;

	void *clt;
	char *extras; // for gui settings
	int indicators;
	int dirty; // for thumbnail
	int dirty_wheel; // is the pitch_weel active

	mandy *mand;
} track;

track *track_new(int port, int channel, int len, int songlen, int ctrlpr);
track *track_clone(track *t);

void track_set_row(track *trk, int c, int n, int type, int note, int velocity, int delay);

void track_free(track *);
void track_clear_rows(track *trk, int c);

void track_add_col(track *trk);
void track_del_col(track *trk, int c);
void track_swap_col(track *trk, int c, int c2);
void track_resize(track *trk, int size);
void track_double(track *trk);
void track_halve(track *trk);

void track_swap_rows(track *trk, int rw1, int rw2);

void track_trigger(track *trk);

void track_add_ctrl(track *trk, int ctl);
void track_del_ctrl(track *trk, int c);
void track_clear_ctrl(track *trk, int c);
void track_swap_ctrl(track *trk, int c, int c2);
void track_ctrl_refresh_envelope(track *trk, int c);

void track_set_ctrl(track *trk, int c, int n, int val);

void track_set_ctrl_num(track *trk, int c, int v);
void track_set_ctrl_row(track *trk, int c, int r, int val, int linked, int smooth);
int track_get_ctrl_row(track *trk, int c, int r, ctrlrow *row);

PyObject *track_get_rec_update(track *trk);

int track_get_last_row_played(track *trk, int col);
void track_insert_rec_update(track *trk, int col, int row);
void track_clear_rec_updates(track *trk);
void track_handle_record(track *trk, midi_event evt);

void track_reset(track *trk);
void track_advance(track *trk, double speriod, jack_nframes_t nframes);
void track_wind(track *trk, double speriod);
void track_kill_notes(track *trk);

void track_set_program(track *trk, int p);
void track_set_bank(track *trk, int msb, int lsb);
char *track_get_program(track *trk);
void track_fix_program_change(track *trk);

void track_set_loop(track *trk, int v);
int track_get_loop(track *trk);

void track_set_qc1(track *trk, int ctrl, int val);
void track_set_qc2(track *trk, int ctrl, int val);

char *track_get_extras(track *trk);
void track_set_extras(track *trk, char *extr);

mandy *track_get_mandy(track *trk);
mandy *track_add_mandy(track *trk);
void track_del_mandy(track *trk);


#endif //__TRACK_H__
