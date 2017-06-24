/* jack_process.h
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

#ifndef __JACK_PROCESS_H__
#define __JACK_PROCESS_H__

#include <jack/jack.h>

int jack_process(jack_nframes_t nframes, void *arg);
int jack_buffer_size_changed(jack_nframes_t nframes, void *arg);

#endif //__JACK_PROCESS_H__
