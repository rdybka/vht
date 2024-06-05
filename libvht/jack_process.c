/* jack_process.c - vahatraker (libvht)
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

#include "jack_process.h"
#include "midi_client.h"
#include "module.h"

int jack_process(jack_nframes_t nframes, void *arg) {
	jack_nframes_t curr_frames;
	jack_time_t curr_usecs;
	jack_time_t next_usecs;

	float period_usecs;

	midi_client *clt = (midi_client *)arg;
	module *mod = (module *)clt->mod_ref;

	jack_get_cycle_times(clt->jack_client, &curr_frames, &curr_usecs, &next_usecs, &period_usecs);
	midi_synch_output_ports(clt);

	if (curr_frames < clt->jack_last_frame) { // drop-out
		curr_frames = clt->jack_last_frame + nframes;
	}

	if (clt->freewheeling) {
		curr_frames = clt->jack_last_frame + nframes;
	}

	module_advance(mod, curr_frames);

	clt->jack_last_frame = curr_frames;

	midi_buffer_flush(clt);

	return 0;
}

int jack_sample_rate_changed(jack_nframes_t srate, void *arg) {
	((midi_client *)arg)->jack_sample_rate = srate;
	return 0;
}

int jack_buffer_size_changed(jack_nframes_t size, void *arg) {
	((midi_client *)arg)->jack_buffer_size = size;
	return 0;
}

int jack_synch_callback(jack_transport_state_t state, jack_position_t *pos, void *arg) {
	midi_client *clt = (midi_client *)arg;
	module *mod = (module *)clt->mod_ref;
	module_synch_transp(mod, state, pos->frame);
	return 1;
}

void jack_port_register_callback(jack_port_id_t port, int reg, void *arg) {
	midi_client *clt = (midi_client *)arg;
	clt->ports_changed = 1;
}
