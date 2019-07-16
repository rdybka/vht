/* libvht.c - Valhalla Tracker (libvht)
 *
 * Copyright (C) 2019 Remigiusz Dybka - remigiusz.dybka@gmail.com
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
#include "jack_client.h"
#include "jack_process.h"

#include "libvht.h"
#include "module.h"

// all wrappers and getters/setters go here, what a mess!

int start(char *name) {
	return jack_start(name);
}

void stop() {
	jack_stop();
}

float module_get_bpm() {
	return module.bpm;
}

int get_jack_max_ports() {
	return JACK_CLIENT_MAX_PORTS;
}

void module_set_bpm(float bpm) {
	module.bpm = bpm;
}

int get_nseq(void) {
	return module.nseq;
}

void module_play(int play) {
	module.playing = play;
	if (play == 0)
		module_mute();
}

int module_is_playing() {
	return module.playing;
}

void module_record(int rec) {
	module.recording = rec;
}

int module_is_recording() {
	return module.recording;
}

int module_get_rpb() {
	return module.rpb;
}

void module_set_rpb(int v) {
	module_excl_in();
	module.rpb = v;
	module_excl_out();
}

void module_reset() {
	module.seq[0]->pos = 0;
	module.zero_time = 0;
	for (int t = 0; t < module.seq[0]->ntrk; t++)
		track_reset(module.seq[0]->trk[t]);
}

struct module_t *get_module(void) {
	return &module;
}

int module_get_nseq(void) {
	return module.nseq;
}

sequence *module_get_seq(int n) {
	return module.seq[n];
}

int module_get_curr_seq() {
	return module.curr_seq;
}

int sequence_get_ntrk(sequence *seq) {
	return seq->ntrk;
}

int sequence_get_length(sequence *seq) {
	return seq->length;
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
}

void track_set_channel(track *trk, int n) {
	trk->channel = n;
}

void track_set_nrows(track *trk, int n) {
	track_resize(trk, n);
}

void track_set_nsrows(track *trk, int n) {
	trk->nsrows = n;
	trk->resync = 1;
}

int module_get_nports() {
	return JACK_CLIENT_MAX_PORTS;
}

char *get_jack_error() {
	return jack_error;
}

double sequence_get_pos(sequence *seq) {
	return seq->pos;
}

void track_set_playing(track *trk, int p) {
	trk->playing = p;
	if (p == 0) {
		track_kill_notes(trk);
	}
}
