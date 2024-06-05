/* jack_process.h - vahatraker (libvht)
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

#ifndef __JACK_PROCESS_H__
#define __JACK_PROCESS_H__

#include <jack/jack.h>

int jack_process(jack_nframes_t nframes, void *arg);
int jack_sample_rate_changed(jack_nframes_t srate, void *arg);
int jack_buffer_size_changed(jack_nframes_t size, void *arg);
int jack_synch_callback(jack_transport_state_t state, jack_position_t *pos, void *arg);
void jack_port_register_callback(jack_port_id_t port, int reg, void *arg);

#endif //__JACK_PROCESS_H__
