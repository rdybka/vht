/* jack_client.c
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
#include <jack/midiport.h>
#include "jack_client.h"
#include "jack_process.h"
#include "module.h"
#include "midi_event.h"

jack_client_t *jack_client;
jack_port_t *jack_output_ports[JACK_CLIENT_MAX_PORTS];
jack_port_t *jack_input_port;
jack_nframes_t jack_sample_rate;
jack_nframes_t jack_buffer_size;
int jack_n_output_ports;
char *jack_error;

int jack_start(char *clt_name) {
	jack_options_t opt;
	opt = JackNoStartServer;

	char *cn = clt_name;
	if (cn == NULL)
		cn = JACK_CLIENT_NAME;

	jack_client = NULL;
	jack_error = NULL;
	if ((jack_client = jack_client_open (cn, opt, NULL)) == 0) {
		jack_error = "Could not connect to JACK. Is server running?";
		fprintf (stderr, "%s\n", jack_error);
		return 1;
	}

	pthread_mutex_init(&module.excl, NULL);
	pthread_mutex_init(&midi_buff_exl, NULL);

	module.jack_running = 1;

	jack_set_process_callback (jack_client, jack_process, 0);
	jack_set_sample_rate_callback(jack_client, jack_sample_rate_changed, 0);
	jack_set_buffer_size_callback(jack_client, jack_buffer_size_changed, 0);

	jack_n_output_ports = 0;
	jack_synch_n_output_ports();

	jack_input_port = jack_port_register (jack_client, "in", JACK_DEFAULT_MIDI_TYPE, JackPortIsInput, 0);

	jack_activate(jack_client);

	return 0;
}

void jack_synch_n_output_ports() {
	if (jack_n_output_ports == module.nports) {
		return;
	}

	if (!module.jack_running)
		return;

	while(module.nports > jack_n_output_ports) {
		char pname[256];
		sprintf(pname, "out_%02d", jack_n_output_ports);
		jack_output_ports[jack_n_output_ports++] = jack_port_register (jack_client, pname, JACK_DEFAULT_MIDI_TYPE, JackPortIsOutput, 0);
	}

	while(module.nports < jack_n_output_ports)
		jack_port_unregister(jack_client, jack_output_ports[--jack_n_output_ports]);
}

void jack_stop() {
	if (!jack_client)
		return;

	jack_client_close(jack_client);
	module.jack_running = 0;
	pthread_mutex_destroy(&module.excl);
	pthread_mutex_destroy(&midi_buff_exl);
}
