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
    int empty = 0;

    if (!passthrough)
        return 0;

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
    return 0;
}
