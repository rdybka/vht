/* libcvht.h - vahatraker (libvht)
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

// behold, the API

#ifndef __LIBCVHT_H__
#define __LIBCVHT_H__

#ifdef SWIG
%module libcvht
%include "carrays.i"
%array_class(int, int_array);
%array_class(double, double_array);
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
extern void module_unpanic(module *mod);
extern int module_is_panicking(module *mod);
extern midi_client *module_get_midi_client(module *mod);
extern int midi_start(midi_client *clt, char *clt_name);
extern void midi_stop(midi_client *clt);
extern char *i2n(unsigned char i);
extern char *get_midi_error(module *mod);
extern char *module_get_time(module *mod);
extern int module_get_max_ports(module *mod);
extern void module_synch_output_ports(module *mod);
extern void set_default_midi_out_port(midi_client *clt, int port);
extern int get_default_midi_out_port(midi_client *clt);

extern void module_play(module *mod, int);
extern void module_set_render_mode(module *mod, int mode);
extern int module_get_render_mode(module *mod);
extern void module_set_render_lead_out(module *mod, int lead_out);
extern void module_set_freewheel(module *mod, int on);
extern int module_is_playing(module *mod);
extern void module_record(module *mod, int);
extern int module_is_recording(module *mod);

extern float module_get_bpm(module *mod);
extern void module_set_bpm(module *mod, float);

extern void module_set_transport(module *mod, int t);
extern int module_get_transport(module *mod);

extern void module_set_pnq_hack(module *mod, int ph);
extern int module_get_pnq_hack(module *mod);
extern void module_set_inception(module *mod, int i);
extern int module_get_inception(module *mod);

extern void module_set_should_save(module *mod, int ss);
extern int module_get_should_save(module *mod);
extern int module_dump_midi(module *mod, const char *phname, int tc, int tpf);
extern int module_get_nseq(module *mod);
extern sequence *module_get_seq(module *mod, int);
extern void module_add_sequence(module *mod, sequence *seq);
extern void module_del_sequence(module *mod, int s);
extern void module_swap_sequence(module *mod, int s1, int s2);
extern sequence *module_sequence_replace(module *mod, int s, sequence *seq);
extern sequence *module_get_curr_seq(module *mod);
extern void module_set_curr_seq(module *mod, int t, int s);
extern void module_dump_notes(module *mod, int n);
extern int module_get_ctrlpr(module *mod);
extern void module_set_ctrlpr(module *mod, int);
extern void module_set_play_mode(module *mod, int m);
extern int module_get_play_mode(module *mod);
extern double module_get_jack_pos(module *mod);
extern int module_get_switch_req(module *mod);
extern PyObject *track_get_rec_update(track *trk);
extern int track_get_last_row_played(track *trk, int col);
extern void track_clear_updates(track *trk);

// midi
extern char *midi_in_get_event(midi_client *clt);
extern void midi_in_clear_events(midi_client *clt);
extern void queue_midi_in(midi_client *clt, int chan, int type, int note, int vel);
extern void midi_ignore_buffer_clear(midi_client *clt);
extern void midi_ignore_buffer_add(midi_client *clt, int channel, int type, int note);

extern void queue_midi_note_on(midi_client *clt, sequence *seq, int port, int chn, int note, int velocity);
extern void queue_midi_note_off(midi_client *clt, sequence *seq, int port, int chn, int note);
extern void queue_midi_ctrl(midi_client *clt, sequence *seq, track *trk, int val, int ctrl);
extern void midi_refresh_port_names(midi_client *clt);
extern int midi_nport_names(midi_client *clt);
extern char *midi_get_port_name(midi_client *clt, int prt);
extern char *midi_get_port_pname(midi_client *clt, jack_port_t *prtref);

extern jack_port_t *midi_get_port_ref(midi_client *clt, char *name);
extern char *midi_get_port_type(jack_port_t *prtref);
extern int midi_get_port_mine(midi_client *clt, jack_port_t *prtref);
extern int midi_get_port_input(jack_port_t *prtref);
extern int midi_get_port_output(jack_port_t *prtref);
extern int midi_get_port_physical(jack_port_t *prtref);

extern const char **midi_get_port_connections(midi_client *clt, jack_port_t *prtref);
extern PyObject *midi_get_props(midi_client *clt);
extern void midi_free_charpp(char **cpp);
extern int charpp_nitems(char **cpp);
extern char *charpp_item(char **cpp, int itm);
extern void midi_port_connect(midi_client *clt, const char *prtref, const char *prtref2);
extern void midi_port_disconnect(midi_client *clt, const char *prtref, const char *prtref2);
extern int midi_port_names_changed(midi_client *clt);
extern int midi_port_is_open(midi_client *clt, int prt);
extern void midi_close_port(midi_client *clt, int prt);
extern void midi_open_port(midi_client *clt, int prt);
extern char *midi_get_output_port_name(midi_client *clt, int prt);
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
extern void sequence_set_pos(sequence *seq, double pos);
extern void sequence_set_midi_focus(sequence *seq, int foc);
extern void sequence_double(sequence *seq);
extern void sequence_halve(sequence *seq);
extern void sequence_set_trg_playmode(sequence *seq, int v);
extern void sequence_set_trg_quantise(sequence *seq, int v);
extern int sequence_get_trg_playmode(sequence *seq);
extern int sequence_get_trg_quantise(sequence *seq);
extern int module_get_max_trg_grp();
extern int sequence_get_trg_grp(sequence *seq, int g);
extern void sequence_set_trg_grp(sequence *seq, int g, int grp);
extern void sequence_set_trig(sequence *seq, int t, int tp, int ch, int nt);
extern char *sequence_get_trig(sequence *seq, int t);
extern void sequence_trigger_mute(sequence *seq, int nframes);
extern void sequence_trigger_mute_forward(sequence *seq, int nframes);
extern void sequence_trigger_mute_back(sequence *seq, int nframes);
extern void sequence_trigger_cue(sequence *seq, int nframes);
extern void sequence_trigger_cue_forward(sequence *seq, int nframes);
extern void sequence_trigger_cue_back(sequence *seq, int nframes);
extern void sequence_trigger_play_on(sequence *seq, int nframes);
extern void sequence_trigger_play_off(sequence *seq, int nframes);
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
extern void sequence_rotate(sequence *seq, int n, int trknum);

extern int sequence_get_loop_active(sequence *seq);
extern void sequence_set_loop_active(sequence *seq, int v);
extern int sequence_get_loop_start(sequence *seq);
extern void sequence_set_loop_start(sequence *seq, int s);
extern int sequence_get_loop_end(sequence *seq);
extern void sequence_set_loop_end(sequence *seq, int e);

extern int sequence_get_next_row(sequence *seq);

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
extern void track_clear_ctrl(track *trk, int c);
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

extern PyObject *track_get_envelope(track *trk, int c);

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
extern void track_set_prog_send(track *trk, int s);
extern int track_get_prog_send(track *trk);
extern char *track_get_program(track *trk);
extern void track_set_qc1_send(track *trk, int s);
extern int track_get_qc1_send(track *trk);
extern void track_set_qc1(track *trk, int ctrl, int val);
extern void track_set_qc2_send(track *trk, int s);
extern int track_get_qc2_send(track *trk);
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

extern mandy *track_get_mandy(track *trk);

// row
extern int row_get_type(row *rw);
extern int row_get_note(row *rw);
extern int row_get_velocity(row *rw);
extern int row_get_delay(row *rw);

extern void row_set_type(row *rw, int type);
extern void row_set_note(row *rw, int note);
extern void row_set_velocity(row *rw, int velocity);
extern void row_set_delay(row *rw, int delay);

extern int row_get_prob(row *rw);
extern void row_set_prob(row *rw, int prob);

extern int row_get_velocity_range(row *rw);
extern int row_get_delay_range(row *rw);
extern void row_set_velocity_range(row *rw, int range);
extern void row_set_delay_range(row *rw, int range);

extern void row_set(row *rw, int type, int note, int velocity, int delay, int prob, int v_r, int d_r);

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
extern timeline *module_get_timeline(module *mod);
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
extern timechange *timeline_change_get_at(timeline *tl, long row, int tol);
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

extern PyObject *mandy_get_pixels(mandy *mand, int width, int height, int stride);
extern unsigned long mandy_render(mandy *mand, int width, int height);
extern unsigned long mandy_get_points(mandy *mand, double *ret_arr, unsigned long l);

extern void mandy_set_rgb(mandy *mand, int r, int g, int b);
extern void mandy_set_xy(mandy *mand, double x, double y);
extern void mandy_set_cxy(mandy *mand, float x, float y);
extern void mandy_set_jxy(mandy *mand, double jx, double jy);

extern void mandy_set_jsx(mandy *mand, double jsx);
extern void mandy_set_jsy(mandy *mand, double jsy);
extern void mandy_set_jvx(mandy *mand, double jvx);
extern void mandy_set_jvy(mandy *mand, double jvy);

extern double mandy_get_jsx(mandy *mand);
extern double mandy_get_jsy(mandy *mand);
extern double mandy_get_jvx(mandy *mand);
extern double mandy_get_jvy(mandy *mand);

extern void mandy_set_pause(mandy *mand, int p);
extern int mandy_get_pause(mandy *mand);
extern void mandy_step(mandy *mand);

extern void mandy_translate(mandy *mand, float x, float y, float w, float h);
extern void mandy_translate_julia(mandy *mand, float x, float y, float w, float h);
extern void mandy_rotate(mandy *mand, float x, float y, float w, float h);
extern void mandy_zoom(mandy *mand, float x, float y, float w, float h);

extern void mandy_set_active(mandy *mand, int active);
extern int mandy_get_active(mandy *mand);

extern char *mandy_get_info(mandy *mand);
extern void mandy_set_info(mandy *mand, char *info);

extern double mandy_get_zoom(mandy *mand);
extern void mandy_set_zoom(mandy *mand, double zoom);
extern double mandy_get_rot(mandy *mand);
extern void mandy_set_rot(mandy *mand, double rot);
extern double mandy_get_bail(mandy *mand);
extern void mandy_set_bail(mandy *mand, double bail);
extern int mandy_get_miter(mandy *mand);
extern void mandy_set_miter(mandy *mand, int miter);
extern int mandy_get_max_iter(mandy *mand);

extern void mandy_set_julia(mandy *mand, int v);
extern int mandy_get_julia(mandy *mand);

extern double mandy_get_max_speed();

extern void mandy_reinit_from_scan(mandy *mand);
extern void mandy_reset(mandy *mand);
extern void mandy_reset_anim(mandy *mand);

extern PyObject *mandy_save(mandy *mand);
extern void mandy_restore(mandy *mand, PyObject *o);

// tracy
extern int mandy_get_ntracies(mandy *mand);
extern tracy *mandy_get_tracy(mandy *mand, int trc_id);
extern tracy *mandy_get_scan_tracy(mandy *mand);
extern tracy *mandy_get_init_tracy(mandy *mand);
extern void mandy_set_follow(mandy *mand, int trc_id);
extern int mandy_get_follow(mandy *mand);

extern PyObject *tracy_get_pos(tracy *trc);
extern PyObject *tracy_get_disp(tracy *trc);
extern PyObject *tracy_get_tail(tracy *trc);
extern double tracy_get_speed(tracy *trc);
extern void tracy_set_speed(tracy *trc, double s);
extern double tracy_get_scale(tracy *trc);
extern void tracy_set_scale(tracy *trc, double s);
extern double tracy_get_phase(tracy *trc);
extern void tracy_set_phase(tracy *trc, double p);
extern double tracy_get_mult(tracy *trc);
extern void tracy_set_mult(tracy *trc, double m);
extern double tracy_get_zoom(tracy *trc);
extern void tracy_set_zoom(tracy *trc, double z);
extern int tracy_get_qnt(tracy *trc);
extern void tracy_set_qnt(tracy *trc, int q);

#endif //__LIBCVHT_H__
