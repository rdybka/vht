/* pms.h
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

#ifndef __LIBPMS_H__
#define __LIBPMS_H__

#ifdef SWIG
%module libpms
%{
#include "libpms.h"
%}
#endif

#include "module.h"

extern int start(char *name);
extern void stop();

extern char *get_jack_error();
extern char *module_get_time();

// module
extern void module_new();
extern void module_free();
extern void module_play(int);
extern int module_is_playing();
extern void module_reset();

extern int module_get_bpm();
extern void module_set_bpm(int);

extern int module_get_nports();
extern void module_set_nports(int);

extern int module_get_nseq();
extern sequence *module_get_seq(int);
extern void module_add_sequence(sequence *seq);
extern void module_del_sequence(int s);
extern void module_swap_sequence(int s1, int s2);

extern void module_dump_notes(int);

// sequence
extern sequence *sequence_new(int length);
extern int sequence_get_ntrk(sequence *seq);
extern int sequence_get_length(sequence *seq);
extern void sequence_set_length(sequence *seq, int length);
extern track *sequence_get_trk(sequence *seq, int n);
extern void sequence_add_track(sequence *seq, track *trk);
extern void sequence_del_track(sequence *seq, int t);
extern void sequence_swap_track(sequence *seq, int t1, int t2);
extern double sequence_get_pos(sequence *seq);

// track
extern row *track_get_row_ptr(track *, int c, int r);
extern int track_get_length(track *trk);
extern int track_get_ncols(track *trk);
extern int track_get_port(track *trk);
extern int track_get_channel(track *trk);
extern int track_get_nrows(track *trk);
extern int track_get_nsrows(track *trk);
extern int track_get_playing(track *trk);
extern double track_get_pos(track *trk);

extern void track_set_port(track *trk, int n);
extern void track_set_channel(track *trk, int n);
extern void track_set_nrows(track *trk, int n);
extern void track_set_nsrows(track *trk, int n);

extern void track_add_col(track *trk);
extern void track_del_col(track *trk, int c);
extern void track_swap_col(track *trk, int c, int c2);
extern void track_resize(track *trk, int size);

extern track *track_new(int port, int channel, int len, int songlen);

// row
extern int row_get_type(row *rw);
extern int row_get_note(row *rw);
extern int row_get_velocity(row *rw);
extern int row_get_delay(row *rw);

extern void row_set_type(row *rw, int type);
extern void row_set_note(row *rw, int note);
extern void row_set_velocity(row *rw, int velocity);
extern void row_set_delay(row *rw, int delay);

extern void row_set(row *rw, int type, int note, int velocity, int delay);

extern int parse_note(char *);
#endif //__LIBPMS_H__
