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

#include <stdio.h>
#include <math.h>
#include "track.h"
#include "module.h"
#include "midi_event.h"
#include "jack_process.h"
#include "jack_client.h"

struct module_t module;

int lastsec;

// the GOD function
void module_advance(void *outp, void *inp, jack_nframes_t curr_frames) {
    // are we muting after stop?
    if (!module.playing && module.mute) {
        jack_midi_clear_buffer(outp);
        midi_buffer_clear();

        for (int t = 0; t < module.seq[module.curr_seq]->ntrk; t++)
            track_kill_notes(module.seq[module.curr_seq]->trk[t]);

        module.mute = 0;
        midi_buffer_flush(outp);
    }

    if (!module.playing) {
        // are we paused?
        if (module.zero_time > 0)
            module.zero_time += jack_buffer_size;

        return;
    }

    if (module.zero_time == 0)
        module.zero_time = curr_frames;

    double time = (curr_frames - module.zero_time) / (double)jack_sample_rate;
    double row_length = 60.0 / ((double)module.rpb * (double)module.bpm);
    double period = ((double)jack_buffer_size / (double)jack_sample_rate) / row_length;

    module.sec = time;
    module.min = module.sec / 60;
    module.sec -= (module.min * 60);

    module.ms = (time - floorf(time)) * 1000;

    jack_midi_clear_buffer(outp);
    midi_buffer_clear();


    //printf("%02d:%02d:%04d\n", module.min, module.sec, module.ms);

    sequence *seq = module.seq[0];
    if (module.playing)
        sequence_advance(seq, period);

// handle input

    jack_nframes_t ninp;
    jack_midi_event_t evt;

    ninp = jack_midi_get_event_count(inp);

    int empty = 0;

    for (jack_nframes_t n = 0; (n < ninp) && !empty; n++) {
        empty = jack_midi_event_get(&evt, inp, n);
        if (!empty) {
            midi_event mev = midi_decode_event(evt.buffer, evt.size);
            mev.time = evt.time;
            midi_buffer_add(mev);
        }
    }

    midi_buffer_flush(outp);

    //printf("time: %02d:%02d:%03d track_pos: %3.3f %3.5f %d\n", module.min, module.sec, module.ms, trk->fpos, period, module.bpm);
    module.song_pos += period;
}

int add_sequence(int seq_clone) {
    // fresh module
    if (module.nseq == 0) {
        module.seq = malloc(sizeof(sequence *));
        module.seq[0] = sequence_new();
        module.nseq = 1;
        return 1;
    }
}

void module_new() {
    module_free();
    module.bpm = 120;
    module.def_nrows = 64;
    module.rpb = 4;
    module.seq = NULL;
    module.nseq = 0;
    module.curr_seq = 0;
    module.playing = 0;
    module.zero_time = 0;
    module.song_pos = 0.0;
    module.mute = 0;

    add_sequence(-1);

    track *trk;
    for (int t = 1; t < 3; t++) {
        //track *trk = track_new(0, t, module.def_nrows, module.def_nrows);
        if (t == 2) {
            trk = track_new(0, t, 3, 8);
            trk->loop = 1;
        } else {
            trk = track_new(0, t, 8, 8);
        }
        if (t == 2)
            trk->loop = 0;
        sequence_add_track(module.seq[0], trk);
    }
}

void module_mute() {
    module.mute = 1;
}

void module_free() {
    // fresh start?
    if (module.bpm == 0) {
        return;
    }

    if (module.seq != NULL) {
        for (int s = 0; s < module.nseq; s++)
            sequence_free(module.seq[s]);

        free(module.seq);
        module.seq = NULL;
        module.bpm = 0;
    }
}
