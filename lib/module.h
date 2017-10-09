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
#include "sequence.h"

struct module_t {
    int playing;
    jack_nframes_t zero_time;
    double song_pos;
    int min, sec, ms;

    int bpm;
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

void module_advance(void *outport, void *inport, jack_nframes_t curr_frames);
void module_new();
void module_free();
void module_mute();
void module_dump_notes(int n);

void module_excl_in();
void module_excl_out();

#endif //__MODULE_H__
