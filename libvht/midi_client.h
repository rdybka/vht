/* midi_client.h - Valhalla Tracker (libvht)
 *
 * Copyright (C) 2020 Remigiusz Dybka - remigiusz.dybka@gmail.com
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

#ifndef __MIDI_CLIENT_H__
#define __MIDI_CLIENT_H__

#define MIDI_CLIENT_NAME 		"valhalla"
#define MIDI_CLIENT_MAX_PORTS	16
#define MIDI_EVT_BUFFER_LENGTH  1023

#include <pthread.h>
#include <jack/jack.h>
#include "sequence.h"
#include "midi_event.h"

/* should be easy enough to refactor this into some kind of driver architecture
have fun! */

typedef struct midi_client_t {
	void *mod_ref;
	int default_midi_port;
	char *error;
	int running;
	int dump_notes;

	jack_client_t *jack_client;
	jack_port_t *jack_input_port;
	int ports_to_open[MIDI_CLIENT_MAX_PORTS];
	jack_port_t *jack_output_ports[MIDI_CLIENT_MAX_PORTS];
	jack_status_t jack_status;
	jack_nframes_t jack_sample_rate;
	jack_nframes_t jack_buffer_size;
	jack_nframes_t jack_last_frame;

	pthread_mutex_t midi_buff_exl;
	pthread_mutex_t midi_in_buff_exl;
	pthread_mutex_t midi_ignore_buff_exl;

	int curr_midi_event[MIDI_CLIENT_MAX_PORTS];
	int curr_midi_queue_event[MIDI_CLIENT_MAX_PORTS];
	int curr_midi_in_event;
	int curr_midi_ignore_event;
	midi_event midi_buffer[MIDI_CLIENT_MAX_PORTS][MIDI_EVT_BUFFER_LENGTH];
	midi_event midi_queue_buffer[MIDI_CLIENT_MAX_PORTS][MIDI_EVT_BUFFER_LENGTH];
	midi_event midi_in_buffer[MIDI_EVT_BUFFER_LENGTH];
	midi_event midi_ignore_buffer[MIDI_EVT_BUFFER_LENGTH];
} midi_client;

midi_client *midi_client_new();
void midi_client_free(midi_client *clt);
int midi_start(midi_client *clt, char *clt_name);
void midi_stop(midi_client *clt);

void midi_synch_output_ports(midi_client *clt);
void midi_in_buffer_add(midi_client *clt, midi_event evt);
void midi_buff_excl_in(midi_client *clt);
void midi_buff_excl_out(midi_client *clt);

void midi_buffer_clear(midi_client *clt);
void midi_buffer_flush(midi_client *clt);
void midi_buffer_add(midi_client *clt, int port, midi_event evt);

void midi_ignore_buff_excl_in(midi_client *clt);
void midi_ignore_buff_excl_out(midi_client *clt);

void queue_midi_note_on(midi_client *clt, sequence *seq, int port, int chn, int note, int velocity);
void queue_midi_note_off(midi_client *clt, sequence *seq, int port, int chn, int note);
void queue_midi_ctrl(midi_client *clt, sequence *seq, track *trk, int val, int ctrl);

#endif //__MIDI_CLIENT_H__
