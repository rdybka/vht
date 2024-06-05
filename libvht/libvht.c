/* libvht.c - vahatraker (libvht)
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
#include <string.h>
#include "midi_client.h"
#include "jack_process.h"

#include "module.h"

// getters/setters and stuff for python

// dear mother of god...
void trk_should_save(track *trk);
void ts_should_save(timestrip *ts);
void tl_should_save(timeline *tl);
void seq_should_save(sequence *seq);

int charpp_nitems(char **cpp) {
	if (!cpp)
		return 0;

	int p = 0;
	while(cpp[p++]);
	return --p;
}

char *charpp_item(char **cpp, int itm) {
	return cpp[itm];
}


midi_client *module_get_midi_client(module *mod) {
	return mod->clt;
}

char *get_midi_error(module *mod) {
	return mod->clt->error;
}

int module_get_max_ports(module *mod) {
	return MIDI_CLIENT_MAX_PORTS;
}

float module_get_bpm(module *mod) {
	return mod->bpm;
}

void module_set_bpm(module *mod, float bpm) {
	mod->bpm = bpm;
	//timeline_change_set(mod->tline, 0, 0, mod->bpm, 0);
}

int module_is_playing(module *mod) {
	return mod->playing;
}

int module_is_panicking(module *mod) {
	return mod->panic;
}

void module_set_render_lead_out(module *mod, int lead_out) {
	mod->render_lead_out = lead_out;
}

void module_record(module *mod, int rec) {
	mod->recording = rec;
}

int module_is_recording(module *mod) {
	return mod->recording;
}


int module_get_nseq(module *mod) {
	return mod->nseq;
}

sequence *module_get_seq(module *mod, int n) {
	return mod->seq[n];
}

int module_get_ctrlpr(module *mod) {
	return mod->ctrlpr;
}

int module_get_switch_req(module *mod) {
	return mod->switch_req;
}

void module_set_ctrlpr(module *mod, int ctrlpr) {
	mod->ctrlpr = ctrlpr;
}

int sequence_get_length(sequence *seq) {
	return seq->length;
}

int sequence_get_index(sequence *seq) {
	return seq->index;
}

int sequence_get_parent(sequence *seq) {
	return seq->parent;
}

void sequence_set_parent(sequence *seq, int s) {
	seq->parent = s;
}

int sequence_get_max_length(void) {
	return SEQUENCE_MAX_LENGTH;
}

track *sequence_get_trk(sequence *seq, int n) {
	return seq->trk[n];
}

row *track_get_row_ptr(track *trk, int c, int r) {
	return &trk->rows[c][r];
}

ctrlrow *track_get_ctrlrow_ptr(track *trk, int c, int r) {
	return &trk->crows[c][r];
}

int track_get_length(track *trk) {
	return trk->nrows;
}

int track_get_ncols(track *trk) {
	return trk->ncols;
}

int track_get_port(track *trk) {
	return trk->port;
}

int track_get_channel(track *trk) {
	return trk->channel;
}

int track_get_index(track *trk) {
	return trk->index;
}

int track_get_nrows(track *trk) {
	return trk->nrows;
}

int track_get_nsrows(track *trk) {
	return trk->nsrows;
}

int track_get_playing(track *trk) {
	return trk->playing;
}

int track_get_nctrl(track *trk) {
	return trk->nctrl;
}

int track_get_ctrlpr(track *trk) {
	return trk->ctrlpr;
}

double track_get_pos(track *trk) {
	return trk->pos;
}

void track_set_port(track *trk, int n) {
	trk->port = n;
	trk_should_save(trk);
}

void track_set_channel(track *trk, int n) {
	trk->channel = n;
	trk_should_save(trk);
}

void track_set_prog_send(track *trk, int s) {
	trk->prog_send = s;
	trk_should_save(trk);
}

int track_get_prog_send(track *trk) {
	return(trk->prog_send);
}

void track_set_program(track *trk, int p) {
	trk->prog = p;
	trk->prog_sent = -1;
	trk_should_save(trk);
}

void track_set_bank(track *trk, int msb, int lsb) {
	trk->bank_msb = msb;
	trk->bank_lsb = lsb;
	trk_should_save(trk);
}

char *track_get_program(track *trk) {
	static char rc[256];
	sprintf(rc, "[%3d, %3d, %3d]", trk->bank_msb, trk->bank_lsb, trk->prog);
	return rc;
}

char *track_get_qc(track *trk) {
	static char rc[256];
	sprintf(rc, "[%3d, %3d, %3d, %3d]", trk->qc1_ctrl, trk->qc1_val, trk->qc2_ctrl, trk->qc2_val);
	return rc;
}

void track_set_qc1_send(track *trk, int s) {
	trk->qc1_send = s;
	trk_should_save(trk);
}

int track_get_qc1_send(track *trk) {
	return(trk->qc1_send);
}

void track_set_qc1(track *trk, int ctrl, int val) {
	trk->qc1_ctrl = ctrl;
	trk->qc1_val = val;
	trk_should_save(trk);
}

void track_set_qc2_send(track *trk, int s) {
	trk->qc2_send = s;
	trk_should_save(trk);
}

int track_get_qc2_send(track *trk) {
	return(trk->qc2_send);
}

void track_set_qc2(track *trk, int ctrl, int val) {
	trk->qc2_ctrl = ctrl;
	trk->qc2_val = val;
	trk_should_save(trk);
}

void track_set_loop(track *trk, int v) {
	trk->loop = v;
	trk_should_save(trk);
}

void track_set_dirty(track *trk, int d) {
	trk->dirty = d;
}

int track_get_dirty(track *trk) {
	return trk->dirty;
}

int track_get_loop(track *trk) {
	return trk->loop;
}

void track_set_indicators(track *trk, int i) {
	trk->indicators = i;
}

void track_clear_indicators(track *trk) {
	trk->indicators = 0;
}


void sequence_set_trg_quantise(sequence *seq, int v) {
	seq->trg_quantise = v;
	seq_should_save(seq);
}

int sequence_get_trg_quantise(sequence *seq) {
	return seq->trg_quantise;
}

void sequence_set_trg_playmode(sequence *seq, int v) {
	seq->trg_playmode = v;
	seq_should_save(seq);
}

int sequence_get_trg_playmode(sequence *seq) {
	return seq->trg_playmode;
}

char *sequence_get_trig(sequence *seq, int t) {
	static char rc[32 * N_TRIGGERS];

	if ((t >= N_TRIGGERS) || (t < 0))
		return "[0,0,0]";

	sprintf(rc, "[%3d, %3d, %3d]", seq->triggers[t].type, seq->triggers[t].channel, seq->triggers[t].note);
	return rc;
}

int module_get_max_trg_grp() {
	return TRIGGER_GROUPS;
}

int sequence_get_trg_grp(sequence *seq, int g) {
	if ((g >= 0) && (g <= 1))
		return seq->trg_grp[g];

	return 0;
}

double sequence_get_pos(sequence *seq) {
	return seq->pos;
}

void sequence_set_pos(sequence *seq, double pos) {
	seq->pos = pos;

	for (int t = 0; t < seq->ntrk; t++) {
		seq->trk[t]->resync = 1;
	}
}


int sequence_get_rpb(sequence *seq) {
	return seq->rpb;
}

void sequence_set_rpb(sequence *seq, int v) {
	seq_mod_excl_in(seq);
	seq->rpb = v;
	seq_mod_excl_out(seq);
}

void sequence_set_lost(sequence *seq, int p) {
	seq->lost = p;
}

void track_set_playing(track *trk, int p) {
	trk->playing = p;
	if (p == 0) {
		track_kill_notes(trk);
	}
}

double timeline_get_length(timeline *tl) {
	return tl->time_length;
}

sequence *timestrip_get_seq(timestrip *tstr) {
	return tstr->seq;
}

int timestrip_get_col(timestrip *tstr) {
	return tstr->col;
}

int timestrip_get_start(timestrip *tstr) {
	return tstr->start;
}

int timestrip_get_length(timestrip *tstr) {
	return tstr->length;
}

int timestrip_get_rpb_start(timestrip *tstr) {
	return tstr->rpb_start;
}

int timestrip_get_rpb_end(timestrip *tstr) {
	return tstr->rpb_end;
}


void timestrip_set_rpb_start(timestrip *tstr, int rpb_start) {
	tstr->rpb_start = rpb_start;
	ts_should_save(tstr);
}

void timestrip_set_rpb_end(timestrip *tstr, int rpb_end) {
	tstr->rpb_end = rpb_end;
	ts_should_save(tstr);
}

void timestrip_set_col(timestrip *tstr, int col) {
	tstr->col = col;
	tstr->seq->parent = col;
	ts_should_save(tstr);
}
