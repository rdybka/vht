/* libcvht.h - Valhalla Tracker (libvht)
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

#ifndef __LIBCVHT_H__
#define __LIBCVHT_H__

#ifdef SWIG
%module libcvht
%include "carrays.i"
%array_class(int, int_array);
%{
#include "libcvht.h"
%}

#endif

#include "module.h"

// module
extern module *module_new(void);
extern void module_free(module *mod);
extern void module_reset(module *mod);
extern void module_panic(module *mod, int brutal);
extern midi_client *module_get_midi_client(module *mod);
extern int midi_start(midi_client *clt, char *clt_name);
extern void midi_stop(midi_client *clt);

extern char *get_midi_error(module *mod);
extern char *module_get_time(module *mod);
extern int module_get_max_ports(module *mod);
extern void module_synch_output_ports(module *mod);

extern void module_play(module *mod, int);
extern int module_is_playing(module *mod);
extern void module_record(module *mod, int);
extern int module_is_recording(module *mod);

extern float module_get_bpm(module *mod);
extern void module_set_bpm(module *mod, float);

extern void module_set_transport(module *mod, int t);
extern int module_get_transport(module *mod);

extern int module_get_nseq(module *mod);
extern sequence *module_get_seq(module *mod, int);
extern void module_add_sequence(module *mod, sequence *seq);
extern void module_del_sequence(module *mod, int s);
extern void module_swap_sequence(module *mod, int s1, int s2);
extern sequence *module_get_curr_seq(module *mod);
extern void module_set_curr_seq(module *mod, int t, int s);
extern void module_dump_notes(module *mod, int n);
extern int module_get_ctrlpr(module *mod);
extern void module_set_ctrlpr(module *mod, int);
extern void module_set_play_mode(module *mod, int m);
extern int module_get_play_mode(module *mod);
extern double module_get_jack_pos(module *mod);
extern int module_get_switch_req(module *mod);
extern char *track_get_rec_update(track *trk);
extern void track_clear_updates(track *trk);

extern char *midi_in_get_event(midi_client *clt);
extern void midi_in_clear_events(midi_client *clt);
extern void midi_ignore_buffer_clear(midi_client *clt);
extern void midi_ignore_buffer_add(midi_client *clt, int channel, int type, int note);

extern void queue_midi_note_on(midi_client *clt, sequence *seq, int port, int chn, int note, int velocity);
extern void queue_midi_note_off(midi_client *clt, sequence *seq, int port, int chn, int note);
extern void queue_midi_ctrl(midi_client *clt, sequence *seq, track *trk, int val, int ctrl);


extern void set_default_midi_port(module *mod, int port);
extern timeline *module_get_timeline(module *mod);

// sequence
extern sequence *sequence_new(int length);
extern int sequence_get_ntrk(sequence *seq);
extern int sequence_get_length(sequence *seq);
extern double sequence_get_relative_length(sequence *seq);
extern int sequence_get_max_length(void);
extern int sequence_get_index(sequence *seq);
extern int sequence_get_parent(sequence *seq);
extern void sequence_set_parent(sequence *seq, int s);
extern void sequence_set_length(sequence *seq, int length);
extern track *sequence_get_trk(sequence *seq, int n);
extern void sequence_add_track(sequence *seq, track *trk);
extern track *sequence_clone_track(sequence *seq, track *trk);
extern void sequence_del_track(sequence *seq, int t);
extern void sequence_swap_track(sequence *seq, int t1, int t2);
extern double sequence_get_pos(sequence *seq);
extern void sequence_set_midi_focus(sequence *seq, int foc);
extern void sequence_double(sequence *seq);
extern void sequence_halve(sequence *seq);
extern void sequence_set_trg_playmode(sequence *seq, int v);
extern void sequence_set_trg_quantise(sequence *seq, int v);
extern int sequence_get_trg_playmode(sequence *seq);
extern int sequence_get_trg_quantise(sequence *seq);

extern void sequence_set_trig(sequence *seq, int t, int tp, int ch, int nt);
extern char *sequence_get_trig(sequence *seq, int t);
extern void sequence_trigger_mute(sequence *seq);
extern void sequence_trigger_cue(sequence *seq);
extern void sequence_trigger_play_on(sequence *seq);
extern void sequence_trigger_play_off(sequence *seq);
extern int sequence_get_playing(sequence *seq);
extern void sequence_set_playing(sequence *seq, int p);
extern void sequence_set_lost(sequence *seq, int p);
extern int sequence_get_rpb(sequence *seq);
extern void sequence_set_rpb(sequence *seq, int rpb);

extern int sequence_get_cue(sequence *seq);
extern sequence *sequence_clone(sequence *seq);
extern void sequence_strip_parent(sequence *seq);

extern int sequence_get_thumb(sequence *seq, int *ret, int l);
extern int sequence_get_thumb_dirty(sequence *seq);
extern int sequence_get_thumb_length(sequence *seq);
extern int sequence_gen_thumb(sequence *seq);

extern char *sequence_get_extras(sequence *seq);
extern void sequence_set_extras(sequence *seq, char *extr);

// track
extern row *track_get_row_ptr(track *, int c, int r);
extern ctrlrow *track_get_ctrlrow_ptr(track *, int c, int r);
extern int track_get_index(track *trk);
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
extern void track_set_playing(track *trk, int p);

extern void track_add_ctrl(track *trk, int ctl);
extern void track_del_ctrl(track *trk, int c);
extern void track_swap_ctrl(track *trk, int c, int c2);
extern void track_set_ctrl(track *trk, int c, int n, int val);

extern void track_get_ctrl(track *tkl, int *ret, int l, int c, int n);
extern void track_get_ctrl_rec(track *tkl, int *ret, int l, int c, int n);
extern void track_get_ctrl_env(track *tkl, int *ret, int l, int c, int n);
extern char *track_get_ctrl_nums(track *trk);

extern void track_set_ctrl_num(track *trk, int c, int v);
extern int track_get_lctrlval(track *trk, int c);
extern void track_ctrl_refresh_envelope(track *trk, int c);

extern int track_get_nctrl(track *trk);
extern int track_get_ctrlpr(track *trk);

extern char *track_get_envelope(track *trk, int c);

extern void track_add_col(track *trk);
extern void track_del_col(track *trk, int c);
extern void track_swap_col(track *trk, int c, int c2);
extern void track_resize(track *trk, int size);
extern void track_double(track *trk);
extern void track_halve(track *trk);
extern void track_trigger(track *trk);
extern void track_kill_notes(track *trk);
extern void track_set_program(track *trk, int p);
extern void track_set_bank(track *trk, int msb, int lsb);
extern char *track_get_program(track *trk);
extern void track_set_qc1(track *trk, int ctrl, int val);
extern void track_set_qc2(track *trk, int ctrl, int val);
extern char *track_get_qc(track *trk);
extern void track_set_loop(track *trk, int v);
extern int track_get_loop(track *trk);
extern int track_get_indicators(track *trk);
extern void track_set_indicators(track *trk, int i);
extern void track_set_dirty(track *trk, int d);
extern int track_get_dirty(track *trk);
extern track *track_new(int port, int channel, int len, int songlen, int ctrlpr);

extern char *track_get_extras(track *trk);
extern void track_set_extras(track *trk, char *extr);
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

// ctrlrow
extern int ctrlrow_get_velocity(ctrlrow *crw);
extern int ctrlrow_get_linked(ctrlrow *crw);
extern int ctrlrow_get_smooth(ctrlrow *crw);
extern int ctrlrow_get_anchor(ctrlrow *crw);

extern void ctrlrow_set_velocity(ctrlrow *crw, int v);
extern void ctrlrow_set_linked(ctrlrow *crw, int l);
extern void ctrlrow_set_smooth(ctrlrow *crw, int s);
extern void ctrlrow_set_anchor(ctrlrow *crw, int a);

extern void ctrlrow_set(ctrlrow *crw, int v, int l, int s, int a);

// timeline
extern void timeline_set_pos(timeline *tl, double npos, int let_ring);
extern double timeline_get_pos(timeline *tl);

extern void timechange_set_bpm(timeline *tl, timechange *tc, float bpm);
extern void timechange_set_row(timeline *tl, timechange *tc, long row);
extern void timechange_set_linked(timeline *tl, timechange *tc, int linked);
extern float timechange_get_bpm(timechange *tc);
extern long timechange_get_row(timechange *tc);
extern int timechange_get_linked(timechange *tc);
extern void timechange_del(timeline *tl, int id);
extern timechange *timeline_get_change(timeline *tl, int id);
extern timechange *timeline_change_get_at(timeline *tl, long row);
extern timechange *timeline_add_change(timeline *tl, float bpm, long row, int linked);
extern int timeline_get_nchanges(timeline *tl);
extern float timeline_get_bpm_at_qb(timeline *tl, long row);
extern int timeline_get_interpol_at_qb(timeline *tl, long row);

extern long timeline_get_qb(timeline *tl, double t);
extern double timeline_get_qb_time(timeline *tl, double row);
extern int timeline_get_nticks(timeline *tl);
extern double timeline_get_tick(timeline *tl, int n);

extern double timeline_get_length(timeline *tl);
extern void timeline_clear(timeline *tl);

extern timestrip *timeline_get_strip(timeline *tl, int n);
extern int timeline_get_nstrips(timeline *tl);
extern timestrip *timeline_add_strip(timeline *tl, int col, sequence *seq, long start, int length, int rpb_start, int rpb_end);
extern int timeline_get_strip_for_qb(timeline *tl, int col, long qb);
extern int timeline_get_last_strip(timeline *tl, int col, long qb);
extern int timeline_expand_start(timeline *tl, long qb_start);
extern int timeline_expand(timeline *tl, long qb_start, long qb_n);

extern void timeline_del_strip(timeline *tl, int id);
extern sequence *timeline_get_seq(timeline *tl, int n);
extern int timeline_get_room(timeline *tl, int col, long qb, int ig);
extern int timeline_get_snap(timeline *tl, int tstr_id, long qb_delta);
extern int timeline_place_clone(timeline *tl, int tstr_id);
extern void timeline_update(timeline *tl);

extern sequence *timestrip_get_seq(timestrip *tstr);
extern int timestrip_get_col(timestrip *tstr);
extern int timestrip_get_start(timestrip *tstr);
extern int timestrip_get_length(timestrip *tstr);
extern int timestrip_get_rpb_start(timestrip *tstr);
extern int timestrip_get_rpb_end(timestrip *tstr);

extern int timestrip_can_resize_seq(timeline *tl, timestrip *tstr, int len);
extern int timestrip_can_rpb_seq(timeline *tl, timestrip *tstr, int rpb);

extern int timestrip_get_enabled(timestrip *tstr);
extern void timestrip_set_enabled(timestrip *tstr, int v);

extern void timestrip_noteoffise(timeline *tl, timestrip *tstr);

extern sequence *timeline_get_prev_seq(timeline *tl, timestrip *tstr);
extern sequence *timeline_get_next_seq(timeline *tl, timestrip *tstr);

extern int timeline_get_loop_active(timeline *tl);
extern void timeline_set_loop_active(timeline *tl, int val);
extern long timeline_get_loop_start(timeline *tl);
extern long timeline_get_loop_end(timeline *tl);
extern void timeline_set_loop_start(timeline *tl, long val);
extern void timeline_set_loop_end(timeline *tl, long val);

extern void timestrip_set_start(timestrip *tstr, int start);
extern void timestrip_set_col(timestrip *tstr, int col);
extern void timestrip_set_length(timestrip *tstr, int length);
extern void timestrip_set_rpb_start(timestrip *tstr, int rpb_start);
extern void timestrip_set_rpb_end(timestrip *tstr, int rpb_end);

extern int parse_note(char *);

#endif //__LIBCVHT_H__
