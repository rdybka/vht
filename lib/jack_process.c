/* jack_process.c
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
#include "jack_process.h"
#include "jack_client.h"
#include "midi_event.h"

int passthrough;

int jack_process(jack_nframes_t nframes, void *arg) {
    void *inp = jack_port_get_buffer(jack_input_port, nframes);
    void *outp = jack_port_get_buffer(jack_output_port, nframes);
    jack_nframes_t ninp;
    jack_midi_event_t evt;

    jack_midi_clear_buffer(outp);

    ninp = jack_midi_get_event_count(inp);

//get timing
    jack_nframes_t curr_frames;
    jack_time_t curr_usecs;
    jack_time_t next_usecs;
    float period_usecs;

    jack_get_cycle_times(jack_client, &curr_frames, &curr_usecs, &next_usecs, &period_usecs);

    if (jack_start_frames == 0)
        jack_start_frames = curr_frames;

    if (jack_start_time == 0)
        jack_start_time = curr_usecs;

    jack_time_t usecs = curr_usecs - jack_start_time;

    int min = 0;
    int sec = 0;
    int ms = 0;

    sec = usecs / 1000000;
    min = sec / 60;
    sec -= (min * 60);

    ms = usecs / 1000;
    ms -= sec * 1000;
    ms -= min * 60000;

    printf("usecs: %10.3f %lu %02d:%02d:%03d\n", period_usecs, curr_frames - jack_start_frames, min, sec, ms);

    if (!passthrough)
        return 0;

    int empty = 0;

    for (jack_nframes_t n = 0; (n < ninp) && !empty; n++) {
        empty = jack_midi_event_get(&evt, inp, n);
        if (!empty) {
            jack_midi_event_write(outp, evt.time, evt.buffer, evt.size);
            midi_event mev = midi_decode_event(evt.buffer, evt.size);
        }
    }

    return 0;
}

int jack_buffer_size_changed(jack_nframes_t nframes, void *arg) {
    jack_buffer_size = nframes;
    printf("jack buffer size:%d\n", jack_buffer_size);
    return 0;
}

int jack_sample_rate_changed(jack_nframes_t nframes, void *arg) {
    jack_sample_rate = nframes;
    printf("jack sample rate:%d\n", jack_sample_rate);
    return 0;
}
