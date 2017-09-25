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

struct module_t module;

int lastsec;

// the GOD function
void module_advance(void *outp, void *inp, jack_nframes_t curr_frames) {
    if (!module.playing)
        return;

    if (module.zero_time == 0)
        module.zero_time = curr_frames;

    float time = (curr_frames - module.zero_time) / (float)jack_sample_rate;
    float row_length = 60.0 / ((float)module.rpb * (float)module.bpm);
    float period = ((float)jack_buffer_size / (float)jack_sample_rate) / row_length;

    module.sec = time;
    module.min = module.sec / 60;
    module.sec -= (module.min * 60);

    module.ms = (time - floorf(time)) * 1000;

    jack_midi_clear_buffer(outp);
    midi_buffer_clear();

    track *trk = module.seq[0]->trk[0];
    track_advance(trk, period);

    /*    if (sec != lastsec) {
            lastsec = sec;

            midi_event evt;

            evt.time = 0;
            evt.channel = 1;
            evt.type = note_on;
            evt.note = 64;
            evt.velocity = 100;

            if (sec%2 == 0)
                evt.type = note_off;

            midi_buffer_add(evt);
        }
    */


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
    module.playing = 1;
    module.zero_time = 0;
    module.song_pos = 0.0;

    add_sequence(-1);
    sequence_add_track(module.seq[0], track_new(0, 1, module.def_nrows, module.def_nrows));
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
