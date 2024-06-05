/* sequence.h - vahatraker (libvht)
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

#ifndef __SEQUENCE_H__
#define __SEQUENCE_H__
#include <pthread.h>
#include <semaphore.h>
#include "midi_event.h"
#include "track.h"


#define SEQUENCE_MAX_LENGTH	1024

#define PLAY_TRIGGER_ONOFF		0
#define PLAY_TRIGGER_ONESHOT	1
#define PLAY_TRIGGER_HOLD		2

#define TRIGGER_MUTE			0
#define TRIGGER_CUE				1
#define TRIGGER_PLAY			2
#define TRIGGER_MUTE_BACK		3
#define TRIGGER_CUE_BACK		4

#define TRIGGER_STATUS_IDLE		0
#define TRIGGER_STATUS_RUN		1
#define TRIGGER_STATUS_SYNC		2
#define TRIGGER_STATUS_KILL		3
#define TRIGGER_STATUS_KILLLATE 4


#define	TRIGGER_GROUPS	5 + 1

#define N_TRIGGERS		5

typedef struct trigger_t {
	int channel;
	int type;
	int note;
} trigger;

typedef struct sequence_t {
	track **trk;
	int ntrk;
	int length;
	int rpb;
	double pos;
	double last_period;
	int midi_focus;
	int parent;
	int index;

	// triggers
	trigger triggers[N_TRIGGERS];
	int trg_times[N_TRIGGERS];
	int trg_status[N_TRIGGERS];
	int trg_grp[2]; // trigger group
	int trg_playmode;
	int trg_quantise;
	pthread_mutex_t *mod_excl;
	int next_row;
	void *clt;
	char *extras;
	int playing;
	int lost;
	int thumb_dirty;
	int *thumb_repr;
	int thumb_last_ring;
	int thumb_length;
	int thumb_panic;
	int loop_active;
	int loop_start;
	int loop_end;
} sequence;

sequence *sequence_new(int length);
void sequence_add_track(sequence *seq, track *trk);
track *sequence_clone_track(sequence *seq, track *trk);
int sequence_get_length(sequence *seq);
double sequence_get_relative_length(sequence *seq);
void sequence_set_length(sequence *seq, int length);
void sequence_del_track(sequence *seq, int t);
void sequence_swap_track(sequence *seq, int t1, int t2);
void sequence_double(sequence *seq);
void sequence_halve(sequence *seq);
void sequence_free(sequence *);
void sequence_advance(sequence *seq, double period, jack_nframes_t nframes);

sequence *sequence_clone(sequence *seq);
void sequence_strip_parent(sequence *seq);

int sequence_get_thumb_dirty(sequence *seq);
int sequence_get_thumb_length(sequence *seq);
int sequence_gen_thumb(sequence *seq);
int sequence_get_thumb(sequence *seq, int *ret, int l);

void sequence_set_trg_quantise(sequence *seq, int v);
void sequence_set_trg_playmode(sequence *seq, int v);
int sequence_get_trg_quantise(sequence *seq);
int sequence_get_trg_playmode(sequence *seq);

int sequence_get_playing(sequence *seq);
void sequence_set_playing(sequence *seq, int p);
void sequence_handle_trigger_event(sequence *seq, midi_event evt);

// nframes = -1 for gui calls
void sequence_trigger_mute(sequence *seq, int nframes);
void sequence_trigger_mute_forward(sequence *seq, int nframes);
void sequence_trigger_mute_back(sequence *seq, int nframes);
void sequence_trigger_cue(sequence *seq, int nframes);
void sequence_trigger_cue_forward(sequence *seq, int nframes);
void sequence_trigger_cue_back(sequence *seq, int nframes);
void sequence_trigger_play_on(sequence *seq, int nframes);
void sequence_trigger_play_off(sequence *seq, int nframes);
void sequence_set_trig(sequence *seq, int t, int tp, int ch, int nt);
char *sequence_get_trig(sequence *seq, int t);

char *sequence_get_extras(sequence *seq);
void sequence_set_extras(sequence *seq, char *extr);

void sequence_rotate(sequence *seq, int n, int trknum); //trknum -1 = all

int sequence_get_loop_active(sequence *seq);
void sequence_set_loop_active(sequence *seq, int v);
int sequence_get_loop_start(sequence *seq);
void sequence_set_loop_start(sequence *seq, int s);
int sequence_get_loop_end(sequence *seq);
void sequence_set_loop_end(sequence *seq, int e);

// internal
void sequence_handle_triggers_post_adv(sequence *seq, double period, int nframes);
void seq_mod_excl_in(sequence *seq);
void seq_mod_excl_out(sequence *seq);
#endif //__SEQUENCE_H__
