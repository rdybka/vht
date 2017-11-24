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

#include "jack_process.h"
#include "jack_client.h"
#include "module.h"

int jack_process(jack_nframes_t nframes, void *arg) {
	jack_nframes_t curr_frames;
	jack_time_t curr_usecs;
	jack_time_t next_usecs;
	float period_usecs;

	//void *outp = jack_port_get_buffer(jack_output_ports[0], nframes);
	//void *inp = jack_port_get_buffer(jack_input_port, nframes);

	jack_get_cycle_times(jack_client, &curr_frames, &curr_usecs, &next_usecs, &period_usecs);
	module_advance(curr_frames);
	return 0;
}

int jack_sample_rate_changed(jack_nframes_t srate, void *arg) {
	jack_sample_rate = srate;
	return 0;
}

int jack_buffer_size_changed(jack_nframes_t size, void *arg) {
	jack_buffer_size = size;
	return 0;
}
