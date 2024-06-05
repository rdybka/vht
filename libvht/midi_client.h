/* midi_client.h - vahatraker (libvht)
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

#ifndef __MIDI_CLIENT_H__
#define __MIDI_CLIENT_H__

#define MIDI_CLIENT_NAME "vahata"
#define MIDI_CLIENT_MAX_PORTS 16
#define MIDI_CLIENT_PORT_NAME "out_%02d"
#define MIDI_EVT_BUFFER_LENGTH 1023

#include <pthread.h>
#include <jack/jack.h>
#include "sequence.h"
#include "midi_event.h"
#include <Python.h>

/* should be easy enough to refactor this into some kind of driver architecture
- have fun! */

typedef struct midi_client_t {
	void *mod_ref;
	int default_midi_port;
	char *error;
	int running;
	int freewheeling;
	int dump_notes;

	jack_client_t *jack_client;
	jack_port_t *jack_input_port;
	int ports_to_open[MIDI_CLIENT_MAX_PORTS];
	int autoports[MIDI_CLIENT_MAX_PORTS];

	jack_port_t *jack_output_ports[MIDI_CLIENT_MAX_PORTS];
	jack_status_t jack_status;
	jack_nframes_t jack_sample_rate;
	jack_nframes_t jack_buffer_size;
	jack_nframes_t jack_last_frame;

	pthread_mutex_t midi_ports_exl;
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
	char *jack_client_name;

	const char **ports;
	int ports_changed;
} midi_client;

midi_client *midi_client_new(void *mod);
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

void midi_send_transp(midi_client *clt, int play, long frames);

void midi_refresh_port_names(midi_client *clt);
int midi_port_names_changed(midi_client *clt);
int midi_nport_names(midi_client *clt);
char *midi_get_port_name(midi_client *clt, int prt);

jack_port_t *midi_get_port_ref(midi_client *clt, char *name);
char *midi_get_port_type(jack_port_t *prtref);
char *midi_get_port_pname(midi_client *clt, jack_port_t *prtref);
int midi_get_port_mine(midi_client *clt, jack_port_t *prtref);
int midi_get_port_input(jack_port_t *prtref);
int midi_get_port_output(jack_port_t *prtref);
int midi_get_port_physical(jack_port_t *prtref);
const char **midi_get_port_connections(midi_client *clt, jack_port_t *prtref);
PyObject *midi_get_props(midi_client *clt);
void midi_free_charpp(char **cpp);
void midi_port_connect(midi_client *clt, const char *prtref, const char *prtref2);
void midi_port_disconnect(midi_client *clt, const char *prtref, const char *prtref2);

// those are for outputs
int midi_port_is_open(midi_client *clt, int prt);
void midi_close_port(midi_client *clt, int prt);
void midi_open_port(midi_client *clt, int prt);
char *midi_get_output_port_name(midi_client *clt, int prt);
void set_default_midi_out_port(midi_client *clt, int port);
int get_default_midi_out_port(midi_client *clt);
void midi_set_freewheel(midi_client *clt, int on);
#endif //__MIDI_CLIENT_H__
