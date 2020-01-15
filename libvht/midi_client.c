/* midi_client.c - Valhalla Tracker (libvht)
 *
 * Copyright (C) 2020 Remigiusz Dybka - remigiusz.dybka@gmail.com
 * @schtixfnord
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
#include <stdlib.h>
#include <jack/midiport.h>
#include "jack_process.h"
#include "module.h"
#include "midi_event.h"
#include "midi_client.h"

midi_client *midi_client_new(void *mod) {
	midi_client *clt = malloc(sizeof(midi_client));
	clt->jack_client = NULL;
	clt->jack_input_port = NULL;
	clt->jack_sample_rate = 0;
	clt->jack_buffer_size = 0;
	clt->jack_last_frame = 0;
	clt->error = NULL;
	clt->default_midi_port = 0;
	clt->mod_ref = mod;
	clt->running = 0;
	clt->dump_notes = 0;

	for (int p = 0; p < MIDI_CLIENT_MAX_PORTS; p++) {
		clt->ports_to_open[p] = 0;
		clt->jack_output_ports[p] = 0;
		clt->curr_midi_event[p] = 0;
		clt->curr_midi_queue_event[p] = 0;
	}

	clt->ports_to_open[0] = 1;
	clt->curr_midi_in_event = 0;
	clt->curr_midi_ignore_event = 0;

	pthread_mutex_init(&clt->midi_buff_exl, NULL);
	pthread_mutex_init(&clt->midi_in_buff_exl, NULL);
	pthread_mutex_init(&clt->midi_ignore_buff_exl, NULL);

	return clt;
}

void midi_client_free(midi_client *clt) {
	if (clt->running)
		midi_stop(clt);

	pthread_mutex_destroy(&clt->midi_buff_exl);
	pthread_mutex_destroy(&clt->midi_ignore_buff_exl);
	pthread_mutex_destroy(&clt->midi_in_buff_exl);
	free(clt);
}

int midi_start(midi_client *clt, char *clt_name) {
	jack_options_t opt;
	opt = JackNoStartServer;

	char *cn = clt_name;
	if (cn == NULL)
		cn = MIDI_CLIENT_NAME;

	clt->jack_client = NULL;
	clt->error = NULL;
	if ((clt->jack_client = jack_client_open (cn, opt, NULL)) == 0) {
		clt->error = "Could not connect to JACK. Is server running?";
		fprintf (stderr, "%s\n", clt->error);
		return 1;
	}

	clt->running = 1;

	for (int p = 0; p < MIDI_CLIENT_MAX_PORTS; p++)
		clt->jack_output_ports[p] = 0;

	clt->jack_input_port = jack_port_register (clt->jack_client, "in", JACK_DEFAULT_MIDI_TYPE, JackPortIsInput, 0);

	clt->curr_midi_in_event = 0;
	clt->default_midi_port = 0;

	midi_synch_output_ports(clt);

	jack_set_process_callback (clt->jack_client, jack_process, clt);
	jack_set_sample_rate_callback(clt->jack_client, jack_sample_rate_changed, clt);
	jack_set_buffer_size_callback(clt->jack_client, jack_buffer_size_changed, clt);

	jack_activate(clt->jack_client);
	return 0;
}

void midi_synch_output_ports(midi_client *clt) {
	for (int p = 0; p < MIDI_CLIENT_MAX_PORTS; p++) {
		if ((clt->ports_to_open[p] == 0) && (clt->jack_output_ports[p])) {
			jack_port_unregister(clt->jack_client, clt->jack_output_ports[p]);
			clt->jack_output_ports[p] = 0;
		}

		if ((clt->ports_to_open[p] == 1) && (clt->jack_output_ports[p] == 0)) {
			char pname[256];
			sprintf(pname, "out_%02d", p);
			clt->jack_output_ports[p] = jack_port_register (clt->jack_client, pname, JACK_DEFAULT_MIDI_TYPE, JackPortIsOutput, 0);
		}
	}

}

void midi_stop(midi_client *clt) {
	if(clt->running)
		jack_client_close(clt->jack_client);

	clt->running = 0;
}

void set_default_midi_port(module *mod, int port) {
	if ((port < 0) || (port >= MIDI_CLIENT_MAX_PORTS))
		return;

	mod->clt->default_midi_port = port;
}


void midi_buff_excl_in(midi_client *clt) {
	pthread_mutex_lock(&clt->midi_buff_exl);
}
void midi_buff_excl_out(midi_client *clt) {
	pthread_mutex_unlock(&clt->midi_buff_exl);
}
void midi_ignore_buff_excl_in(midi_client *clt) {
	pthread_mutex_lock(&clt->midi_ignore_buff_exl);
}
void midi_ignore_buff_excl_out(midi_client *clt) {
	pthread_mutex_unlock(&clt->midi_ignore_buff_exl);
}
void midi_in_buff_excl_in(midi_client *clt) {
	pthread_mutex_lock(&clt->midi_in_buff_exl);
}
void midi_in_buff_excl_out(midi_client *clt) {
	pthread_mutex_unlock(&clt->midi_in_buff_exl);
}

void midi_buffer_clear(midi_client *clt) {
	for (int i = 0; i < MIDI_CLIENT_MAX_PORTS; i++)
		clt->curr_midi_event[i] = 0;
}

void midi_buffer_add(midi_client *clt, int port, midi_event evt) {
	if (clt->curr_midi_event[port] == MIDI_EVT_BUFFER_LENGTH)
		return;

	clt->midi_buffer[port][clt->curr_midi_event[port]++] = evt;
}

int midi_buffer_compare(const void *a, const void *b) {
	return ((midi_event *)a)->time - ((midi_event *)b)->time;
}

void midi_buffer_flush_port(midi_client *clt, int port) {
	void *outp = jack_port_get_buffer(clt->jack_output_ports[port], clt->jack_buffer_size);
	jack_midi_clear_buffer(outp);

	midi_buff_excl_in(clt);
	for (int f = 0; f < clt->curr_midi_queue_event[port]; f++) {
		midi_buffer_add(clt, port, clt->midi_queue_buffer[port][f]);
	}

	clt->curr_midi_queue_event[port] = 0;
	midi_buff_excl_out(clt);

	if (clt->curr_midi_event[port] == 0)
		return;

	qsort(clt->midi_buffer[port], clt->curr_midi_event[port], sizeof(midi_event), midi_buffer_compare);

	for (int i = 0; i < clt->curr_midi_event[port]; i++) {
		unsigned char buff[3];
		if (midi_encode_event(clt->midi_buffer[port][i], buff)) {
			int l = 3;

			if (clt->midi_buffer[port][i].type == program_change) {
				l = 2;
			}

			jack_midi_event_write(outp, clt->midi_buffer[port][i].time, buff, l);
		}

		module *mod = (module *) clt->mod_ref;

		if (clt->dump_notes) {
			char desc[256];
			midi_describe_event(clt->midi_buffer[port][i], desc, 256);
			printf("%02d:%02d:%03d pt: %02d, %s\n", mod->min, mod->sec, mod->ms, port, desc);
		}

	}
}

void midi_buffer_flush(midi_client *clt) {
	for (int p = 0; p < MIDI_CLIENT_MAX_PORTS; p++) {
		if (clt->jack_output_ports[p])
			midi_buffer_flush_port(clt, p);
	}
}


void queue_midi_note_on(midi_client *clt, sequence *seq, int port, int chn, int note, int velocity) {
	midi_event evt;
	evt.type = note_on;
	evt.channel = chn;
	evt.note = note;
	evt.velocity = velocity;
	evt.time = 0;

	module *mod = (module *) clt->mod_ref;

	if (mod->recording && mod->playing) {
		jack_nframes_t jft = jack_frame_time(clt->jack_client);
		evt.time = jft - clt->jack_last_frame;

		if (jft < clt->jack_last_frame)
			evt.time = 0;

		if (seq)
			sequence_handle_record(mod, seq, evt);
	}

	midi_buff_excl_in(clt);
	clt->midi_queue_buffer[port][clt->curr_midi_queue_event[port]++] = evt;
	midi_buff_excl_out(clt);
}

void queue_midi_note_off(midi_client *clt, sequence *seq, int port, int chn, int note) {
	midi_event evt;
	evt.type = note_off;
	evt.channel = chn;
	evt.note = note;
	evt.velocity = 0;
	evt.time = 0;

	module *mod = (module *) clt->mod_ref;

	if (mod->recording && mod->playing) {
		jack_nframes_t jft = jack_frame_time(clt->jack_client);
		evt.time = jft - clt->jack_last_frame;

		if (jft < clt->jack_last_frame) {
			evt.time = 0;
		}

		if (seq)
			sequence_handle_record(mod, seq, evt);
	}

	midi_buff_excl_in(clt);
	clt->midi_queue_buffer[port][clt->curr_midi_queue_event[port]++] = evt;
	midi_buff_excl_out(clt);
}

void queue_midi_ctrl(midi_client *clt, sequence *seq, track *trk, int val, int ctrl) {
	midi_event evt;
	evt.type = pitch_wheel;
	evt.channel = trk->channel;
	evt.note = 0;
	evt.velocity = val;
	evt.time = 0;

	module *mod = (module *) clt->mod_ref;

	if (ctrl > -1) {
		evt.type = control_change;
		evt.note = ctrl;
	}

	if (mod->recording && mod->playing) {
		jack_nframes_t jft = jack_frame_time(clt->jack_client);
		evt.time = jft - clt->jack_last_frame;

		if (jft < clt->jack_last_frame)
			evt.time = 0;

		if (seq)
			sequence_handle_record(mod, seq, evt);
	}

	// update lctrlvals in track
	pthread_mutex_lock(&trk->exclctrl);
	if (ctrl == -1) {
		trk->lctrlval[0] = val * 127;
	} else {
		for (int c = 0; c < trk->nctrl; c++) {
			if (trk->ctrlnum[c] == ctrl)
				trk->lctrlval[c] = val;
		}
	}

	pthread_mutex_unlock(&trk->exclctrl);

	midi_buff_excl_in(clt);
	clt->midi_queue_buffer[trk->port][clt->curr_midi_queue_event[trk->port]++] = evt;
	midi_buff_excl_out(clt);
}

void midi_in_buffer_add(midi_client *clt, midi_event evt) {
	midi_in_buff_excl_in(clt);
	if (clt->curr_midi_in_event == MIDI_EVT_BUFFER_LENGTH) {
		midi_in_buff_excl_out(clt);
		return;
	}

	clt->midi_in_buffer[clt->curr_midi_in_event++] = evt;
	midi_in_buff_excl_out(clt);
}

char *midi_in_get_event(midi_client *clt) {
	if (clt->curr_midi_in_event == 0)
		return NULL;

	midi_in_buff_excl_in(clt);
	midi_event evt = clt->midi_in_buffer[--clt->curr_midi_in_event];

	static char buff[1024];
	sprintf(buff, "{\"channel\" :%d, \"type\" :%d, \"note\" : %d, \"velocity\" : %d, \"time\" : %d}", evt.channel, evt.type, evt.note, evt.velocity, evt.time);
	midi_in_buff_excl_out(clt);
	return buff;
}

void midi_in_clear_events(midi_client *clt) {
	midi_in_buff_excl_in(clt);
	clt->curr_midi_in_event = 0;
	midi_in_buff_excl_out(clt);
}

void midi_ignore_buffer_clear(midi_client *clt) {
	midi_ignore_buff_excl_in(clt);
	clt->curr_midi_ignore_event = 0;
	midi_ignore_buff_excl_out(clt);
}

void midi_ignore_buffer_add(midi_client *clt, int channel, int type, int note) {
	midi_event evt;
	evt.channel = channel;
	evt.type = type;
	evt.note = note;
	evt.velocity = evt.time = 0;

	midi_ignore_buff_excl_in(clt);
	clt->midi_ignore_buffer[clt->curr_midi_ignore_event++] = evt;
	midi_ignore_buff_excl_out(clt);
}

