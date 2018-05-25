/* module.h
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

#ifndef __MODULE_H__
#define __MODULE_H__

#include <stdlib.h>
#include <jack/jack.h>
#include <jack/midiport.h>
#include <pthread.h>
#include "midi_event.h"
#include "sequence.h"

struct module_t {
	int playing;

	int recording;

	jack_nframes_t zero_time;
	double song_pos;
	int min, sec, ms;

	int bpm; // why is this an int ?!?!?!?
	int rpb; // rows per beat

	int def_nrows;
	sequence **seq;
	int nseq;
	int curr_seq;
	int mute;

	int jack_running;
	int dump_notes;
	pthread_mutex_t excl; // to block structural changes when jack thread advances module
};

extern struct module_t module;

void module_advance(jack_nframes_t curr_frames);
void module_new(void);
void module_free(void);
void module_mute(void);
void module_dump_notes(int n);

void module_excl_in(void);
void module_excl_out(void);

void module_add_sequence(sequence *seq);
void module_del_sequence(int s);
void module_swap_sequence(int s1, int s2);
char *modue_get_time(void);

#endif //__MODULE_H__
