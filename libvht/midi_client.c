/* midi_client.c - vahatraker (libvht)
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

#include <stdio.h>
#include <stdlib.h>
#include <jack/midiport.h>
#include <jack/metadata.h>
#include <jack/uuid.h>
#include <errno.h>
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
	clt->freewheeling = 0;
	clt->dump_notes = 0;
	clt->ports = 0;
	clt->ports_changed = 0;
	clt->jack_client_name = 0;

	for (int p = 0; p < MIDI_CLIENT_MAX_PORTS; p++) {
		clt->ports_to_open[p] = 0;
		clt->autoports[p] = 0;
		clt->jack_output_ports[p] = 0;
		clt->curr_midi_event[p] = 0;
		clt->curr_midi_queue_event[p] = 0;
	}

	clt->ports_to_open[0] = 1;
	clt->curr_midi_in_event = 0;
	clt->curr_midi_ignore_event = 0;

	pthread_mutex_init(&clt->midi_ports_exl, NULL);
	pthread_mutex_init(&clt->midi_buff_exl, NULL);
	pthread_mutex_init(&clt->midi_in_buff_exl, NULL);
	pthread_mutex_init(&clt->midi_ignore_buff_exl, NULL);

	return clt;
}

void midi_client_free(midi_client *clt) {
	if (clt->running)
		midi_stop(clt);

	pthread_mutex_destroy(&clt->midi_ports_exl);
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

	clt->jack_client_name = jack_get_client_name(clt->jack_client);

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
	jack_set_sync_callback(clt->jack_client, jack_synch_callback, clt);
	jack_set_port_registration_callback(clt->jack_client, jack_port_register_callback, clt);
	jack_activate(clt->jack_client);

	midi_refresh_port_names(clt);
	return 0;
}

void midi_close_port(midi_client *clt, int prt) {
	if (prt < 0 || prt >= MIDI_CLIENT_MAX_PORTS)
		return;

	//printf("close %d\n", prt);

	clt->ports_to_open[prt] = 0;
	midi_synch_output_ports(clt);
};

void midi_open_port(midi_client *clt, int prt) {
	if (prt < 0 || prt >= MIDI_CLIENT_MAX_PORTS)
		return;

	if (clt->jack_output_ports[prt])
		return;

	char pname[32];
	sprintf(pname, MIDI_CLIENT_PORT_NAME, prt);
	clt->jack_output_ports[prt] = jack_port_register (clt->jack_client, pname, JACK_DEFAULT_MIDI_TYPE, JackPortIsOutput, 0);
	clt->ports_to_open[prt] = 1;
	midi_synch_output_ports(clt);

	//printf("open %d - %s\n", prt, pname);
};

int midi_port_is_open(midi_client *clt, int prt) {
	if (prt < 0 || prt >= MIDI_CLIENT_MAX_PORTS)
		return 0;

	if (clt->jack_output_ports[prt])
		return 1;

	return 0;
}

void midi_ports_excl_in(midi_client *clt) {
	pthread_mutex_lock(&clt->midi_ports_exl);
}

void midi_ports_excl_out(midi_client *clt) {
	pthread_mutex_unlock(&clt->midi_ports_exl);
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

void midi_synch_output_ports(midi_client *clt) {
	midi_ports_excl_in(clt);
	clt->autoports[0] = 1;

	for (int p = 0; p < MIDI_CLIENT_MAX_PORTS; p++) {
		if ((clt->autoports[p] == 0) && (clt->ports_to_open[p] == 0) && (clt->jack_output_ports[p])) {
			jack_port_unregister(clt->jack_client, clt->jack_output_ports[p]);
			clt->jack_output_ports[p] = 0;
		}

		if ((clt->autoports[p] == 1) && (clt->jack_output_ports[p] == 0)) {
			char pname[32];
			sprintf(pname, MIDI_CLIENT_PORT_NAME, p);
			clt->jack_output_ports[p] = jack_port_register (clt->jack_client, pname, JACK_DEFAULT_MIDI_TYPE, JackPortIsOutput, 0);
		}
	}

	set_default_midi_out_port(clt, clt->default_midi_port);

	midi_ports_excl_out(clt);
}

void midi_stop(midi_client *clt) {
	if(clt->running) {
		if (clt->ports) {
			jack_free(clt->ports);
			clt->ports = 0;
		}
		jack_client_close(clt->jack_client);
	}

	clt->running = 0;
}

void set_default_midi_port(module *mod, int port) {
	if ((port < 0) || (port >= MIDI_CLIENT_MAX_PORTS))
		return;

	mod->clt->default_midi_port = port;
}

void midi_buffer_clear(midi_client *clt) {
	for (int i = 0; i < MIDI_CLIENT_MAX_PORTS; i++)
		clt->curr_midi_event[i] = 0;
}

void midi_buffer_add(midi_client *clt, int port, midi_event evt) {
	if (clt->curr_midi_event[port] == MIDI_EVT_BUFFER_LENGTH)
		return;

	module *mod = (module *) clt->mod_ref;
	if (mod->panic && evt.type == note_on)
		return;

	clt->midi_buffer[port][clt->curr_midi_event[port]++] = evt;
}

int midi_buffer_compare(const void *a, const void *b) {
	int res = ((midi_event *)a)->time - ((midi_event *)b)->time;

	if (res == 0)
		res = ((midi_event *)a)->channel - ((midi_event *)b)->channel;

	if (res == 0)
		res = ((midi_event *)b)->type - ((midi_event *)a)->type;

	if (res == 0)
		res = ((midi_event *)a)->note - ((midi_event *)b)->note;

	if (res == 0)
		res = ((midi_event *)b)->velocity - ((midi_event *)a)->velocity;

	return res;
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

	if (clt->curr_midi_event[port] > 1)
		qsort(clt->midi_buffer[port], clt->curr_midi_event[port], sizeof(midi_event), midi_buffer_compare);

	for (int i = 0; i < clt->curr_midi_event[port]; i++) {
		midi_event *last = 0;
		unsigned char buff[3];
		int dbl = 0;

		midi_event *curr = &clt->midi_buffer[port][i];
		if (curr->time >= clt->jack_buffer_size) {
			curr->time = clt->jack_buffer_size - 1;
		}

		if (midi_encode_event(clt->midi_buffer[port][i], buff)) {
			int l = 3;

			if (clt->midi_buffer[port][i].type == program_change) {
				l = 2;
			}

			if (last) {
				curr = &clt->midi_buffer[port][i];

				if ((last->time == curr->time) &&
				        (last->channel == curr->channel) &&
				        (last->type == curr->type) &&
				        (last->note == curr->note)) {
					dbl = 1;
					printf("dbl!!!\n");
				}

				if (!dbl)
					jack_midi_event_write(outp, clt->midi_buffer[port][i].time, buff, l);

				last = &clt->midi_buffer[port][i];
			} else {
				jack_midi_event_write(outp, clt->midi_buffer[port][i].time, buff, l);
				last = &clt->midi_buffer[port][i];
			}
		}

		module *mod = (module *) clt->mod_ref;
		if (mod->midi_file) {
			smf_client_flush(mod->midi_file, port, clt->midi_buffer[port][i]);
		}

		if (clt->dump_notes && !dbl) {
			char desc[256];
			midi_describe_event(clt->midi_buffer[port][i], desc, 256);
			printf("%02d:%02d:%03d >> pt: %02d, %s\n", mod->min, mod->sec, mod->ms, port, desc);
		}

	}
}

void midi_buffer_flush(midi_client *clt) {
	for (int p = 0; p < MIDI_CLIENT_MAX_PORTS; p++) {
		if (clt->jack_output_ports[p])
			midi_buffer_flush_port(clt, p);
	}

	midi_buffer_clear(clt);
}

void queue_midi_note_on(midi_client *clt, sequence *seq, int port, int chn, int note, int velocity) {
	midi_event evt;
	evt.type = note_on;
	evt.channel = chn;
	evt.note = note;
	evt.velocity = velocity;
	evt.time = -1;

	module *mod = (module *) clt->mod_ref;

	if (seq->midi_focus > -1) {
		module_handle_inception(seq->trk[seq->midi_focus], evt);
	}

	evt.time = 0;

	if (mod->recording && mod->playing) {
		jack_nframes_t jft = jack_frame_time(clt->jack_client);
		evt.time = jft - clt->jack_last_frame;

		if (jft < clt->jack_last_frame)
			evt.time = 0;

		if (seq)
			sequence_handle_record(mod, seq, evt);
	} else {
		midi_buff_excl_in(clt);
		clt->midi_queue_buffer[port][clt->curr_midi_queue_event[port]++] = evt;
		midi_buff_excl_out(clt);
	}
}

void queue_midi_note_off(midi_client *clt, sequence *seq, int port, int chn, int note) {
	midi_event evt;
	evt.type = note_off;
	evt.channel = chn;
	evt.note = note;
	evt.velocity = 0;
	evt.time = -1;

	module *mod = (module *) clt->mod_ref;

	if (seq->midi_focus > -1) {
		module_handle_inception(seq->trk[seq->midi_focus], evt);
	}

	evt.time = 0;

	if (mod->recording && mod->playing) {
		jack_nframes_t jft = jack_frame_time(clt->jack_client);
		evt.time = jft - clt->jack_last_frame;

		if (jft < clt->jack_last_frame) {
			evt.time = 0;
		}

		if (seq)
			sequence_handle_record(mod, seq, evt);
	} else {
		midi_buff_excl_in(clt);
		clt->midi_queue_buffer[port][clt->curr_midi_queue_event[port]++] = evt;
		midi_buff_excl_out(clt);
	}
}

void queue_midi_ctrl(midi_client *clt, sequence *seq, track *trk, int val, int ctrl) {
	midi_event evt;
	evt.type = control_change;
	evt.channel = trk->channel;
	evt.note = ctrl;
	evt.velocity = val;
	evt.time = -1;

	module *mod = (module *) clt->mod_ref;

	if (seq->midi_focus > -1) {
		module_handle_inception(seq->trk[seq->midi_focus], evt);
	}

	evt.time = 0;

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
	} else {
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

void queue_midi_in(midi_client *clt, int chan, int type, int note, int vel) {
	midi_event evt;
	evt.type = type;
	evt.channel = chan;
	evt.note = note;
	evt.velocity = vel;
	midi_in_buffer_add(clt, evt);
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

void midi_send_transp(midi_client *clt, int play, long frames) {
	//printf("transp: %d %ld\n", play, frames);
	jack_position_t pos;
	pos.frame = frames;
	pos.valid = 0;

	if (frames > -1) {
		jack_transport_reposition(clt->jack_client, &pos);
	}

	if (play) {
		jack_transport_start(clt->jack_client);
	} else {
		jack_transport_stop(clt->jack_client);
	}
}

void midi_refresh_port_names(midi_client *clt) {
	midi_ports_excl_in(clt);
	if (clt->ports)
		jack_free(clt->ports);

	if (clt->jack_client)
		clt->ports = jack_get_ports(clt->jack_client, 0, 0, 0);

	clt->ports_changed = 0;
	midi_ports_excl_out(clt);
}

int midi_nport_names(midi_client *clt) {
	if (!clt->ports)
		return 0;

	int p = 0;
	while(clt->ports[p++]);
	return --p;
}

char *midi_get_port_name(midi_client *clt, int prt) {
	static char buff[1023];

	if (prt >= midi_nport_names(clt)) {
		return NULL;
	}

	strcpy(buff, clt->ports[prt]);
	return buff;
}

char *midi_get_port_pname(midi_client *clt, jack_port_t *prtref) {
	static char buff[1023];

	jack_uuid_t uuid = jack_port_uuid(prtref);
	char *val = 0;
	char *type = 0;
	if (0 == jack_get_property(uuid, JACK_METADATA_PRETTY_NAME, &val, &type)) {
		strcpy(buff, val);
	} else {
		buff[0] = 0;
	}

	if (val)
		jack_free(val);
	if (type)
		jack_free(type);

	return buff;
}

jack_port_t *midi_get_port_ref(midi_client *clt, char *name) {
	return jack_port_by_name(clt->jack_client, name);
}

char *midi_get_port_type(jack_port_t *prtref) {
	static char buff[1023];
	const char *t = jack_port_type(prtref);
	if (t) {
		strcpy(buff, t);
		return buff;
	}

	return NULL;
}

int midi_get_port_mine(midi_client *clt, jack_port_t *prtref) {
	return jack_port_is_mine(clt->jack_client, prtref);
}

int midi_get_port_input(jack_port_t *prtref) {
	return jack_port_flags(prtref) & JackPortIsInput;
}

int midi_get_port_output(jack_port_t *prtref) {
	return jack_port_flags(prtref) & JackPortIsOutput;
}

int midi_get_port_physical(jack_port_t *prtref) {
	return jack_port_flags(prtref) & JackPortIsPhysical;
}

const char **midi_get_port_connections(midi_client *clt, jack_port_t *prtref) {
	return jack_port_get_all_connections(clt->jack_client, prtref);
}

void midi_free_charpp(char **cpp) {
	if (cpp)
		jack_free(cpp);
}

PyObject *midi_get_props(midi_client *clt) {


	return NULL;
}

void midi_port_connect(midi_client *clt, const char *prtref, const char *prtref2) {
	int stat = jack_connect(clt->jack_client, prtref, prtref2);
	if (stat == EEXIST)
		stat = 0;
}

void midi_port_disconnect(midi_client *clt, const char *prtref, const char *prtref2) {
	jack_disconnect(clt->jack_client, prtref, prtref2);
}

int midi_port_names_changed(midi_client *clt) {
	if (clt->ports_changed) {
		midi_refresh_port_names(clt);
		return 1;
	} else {
		return 0;
	}
}

char *midi_get_output_port_name(midi_client *clt, int prt) {
	if (prt < 0 || prt >= MIDI_CLIENT_MAX_PORTS)
		return NULL;

	static char pname[256];
	char buff[256];
	pname[0] = 0;
	sprintf(buff, "%s:", clt->jack_client_name);
	strcat(pname, buff);
	sprintf(buff, MIDI_CLIENT_PORT_NAME, prt);
	strcat(pname, buff);
	return pname;
}

void set_default_midi_out_port(midi_client *clt, int port) {
	if (port == clt->default_midi_port)
		if (midi_port_is_open(clt, port))
			return;

	int p = port;
	int search_up = 1;

	if (p < clt->default_midi_port)
		search_up = 0;

	if (p < 0)
		p = MIDI_CLIENT_MAX_PORTS - 1;

	if (p >= MIDI_CLIENT_MAX_PORTS)
		p = 0;

	while(!midi_port_is_open(clt, p) && p != 0) {
		if (search_up) {
			p++;
		} else {
			p--;
		}

		if (p >= MIDI_CLIENT_MAX_PORTS)
			p = 0;

		if (p < 0)
			p = MIDI_CLIENT_MAX_PORTS - 1;
	}

	clt->default_midi_port = p;
}

int get_default_midi_out_port(midi_client *clt) {
	return clt->default_midi_port;
}

void midi_set_freewheel(midi_client *clt, int on) {
	clt->freewheeling = on;
	jack_set_freewheel(clt->jack_client, on);
}
