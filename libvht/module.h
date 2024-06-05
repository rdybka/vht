/* module.h - vahatraker (libvht)
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

#ifndef __MODULE_H__
#define __MODULE_H__

#include <stdlib.h>
#include <jack/jack.h>
#include <jack/midiport.h>
#include <pthread.h>
#include "midi_event.h"
#include "midi_client.h"
#include "sequence.h"
#include "timeline.h"
#include "smf.h"

#define DEFAULT_CTRLPR 16

typedef struct module_t {
	int playing;
	int recording;

	jack_nframes_t zero_time;

	double song_pos;
	int min, sec, ms;

	float bpm;

	int ctrlpr;
	sequence **seq;
	timeline *tline;
	int nseq;
	sequence *curr_seq;
	int mute;

	int cur_rec_update;
	pthread_mutex_t excl;
	midi_client *clt;
	smf *midi_file;
	int play_mode; // 0 - seq_loop, 1 - timeline
	int panic;
	double switch_delay;
	int switch_req;
	int transp;
	int render_mode;
	jack_nframes_t end_time;
	int render_lead_out;
	int pnq_hack;
	int inception;
	int should_save;
} module;

module *module_new(void);
void module_play(module *mod, int);
void module_free(module *mod);
void module_handle_inception(track *trk, midi_event evt);
void module_advance(module *mod, jack_nframes_t curr_frames);
void module_mute(module *mod);
void module_reset(module *mod);
void module_dump_notes(module *mod, int n);
int module_dump_midi(module *mod, const char *phname, int tc, int tpf);
void module_excl_in(module *mod);
void module_excl_out(module *mod);

void module_synch_transp(module *mod, int play, jack_nframes_t frames);
void module_send_transp(module *mod, int play, jack_nframes_t frames);

void module_add_sequence(module *mod, sequence *seq);
void module_del_sequence(module *mod, int s);
void module_swap_sequence(module *mod, int s1, int s2);
sequence *module_sequence_replace(module *mod, int s, sequence *seq);
char *modue_get_time(module *mod);
double module_get_jack_pos(module *mod);
void module_synch_output_ports(module *mod);

void module_set_play_mode(module *mod, int m);
int module_get_play_mode(module *mod);

void module_set_transport(module *mod, int t);
int module_get_transport(module *mod);

void sequence_handle_record(module *mod, sequence *seq, midi_event evt);
void module_panic(module *mod, int brutal);
void module_unpanic(module *mod);

void module_set_render_mode(module *mod, int mode);
int module_get_render_mode(module *mod);

void module_set_render_lead_out(module *mod, int lead_out);
void module_set_freewheel(module *mod, int on);

void module_seq_pnq_hack(module *mod, int ph);
int module_get_pnq_hack(module *mod);

void module_set_should_save(module *mod, int ss);
int module_get_should_save(module *mod);

#endif //__MODULE_H__
