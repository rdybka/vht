/* midi_event.c
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
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <jack/midiport.h>
#include "jack_client.h"
#include "midi_event.h"
#include "module.h"

midi_event midi_buffer[JACK_CLIENT_MAX_PORTS][EVT_BUFFER_LENGTH];
midi_event midi_queue_buffer[JACK_CLIENT_MAX_PORTS][EVT_BUFFER_LENGTH];

midi_event midi_in_buffer[EVT_BUFFER_LENGTH];
int curr_midi_in_event;

int curr_midi_event[JACK_CLIENT_MAX_PORTS];
int curr_midi_queue_event[JACK_CLIENT_MAX_PORTS];

pthread_mutex_t midi_buff_exl;

void midi_buff_excl_in() {
	pthread_mutex_lock(&midi_buff_exl);
}

void midi_buff_excl_out() {
	pthread_mutex_unlock(&midi_buff_exl);
}

int midi_encode_event(midi_event evt, unsigned char *buff) {
	if (evt.type == none)
		return 0;

	switch(evt.type) {
	case note_off:
		buff[0] = 0x80;
		break;
	case note_on:
		buff[0] = 0x90;
		break;
	case control_change:
		buff[0] = 0xB0;
		break;
	case pitch_wheel:
		buff[0] = 0xE0;
		break;
	}

	buff[0]+= evt.channel - 1;
	buff[1] = evt.note;
	buff[2] = evt.velocity;

	return 1;
}

midi_event midi_decode_event(unsigned char *data, int len) {
	midi_event ret;
	ret.type = none;

	if (len != 3) {
		return ret;
	}

	//printf("%x %x %x\n", data[0], data[1], data[2]);

	if (!(data[0] & 0x80))
		return ret;

	ret.channel = (data[0] & 0x0f) + 1;

	switch((data[0] & 0x70) >> 4) {
	case 0:
		ret.type = note_off;
		break;
	case 1:
		ret.type = note_on;
		break;
	case 3:
		ret.type = control_change;
		break;
	case 6:
		ret.type = pitch_wheel;
		break;
	}

	ret.note = data[1];
	ret.velocity = data[2];
	ret.time = 0;

	return ret;
}

char *midi_describe_event(midi_event evt, char *buff, int len) {
	buff[0] = 0;

	char *b;
	switch(evt.type) {
	case none:
		b = "none";
		break;
	case note_on:
		b = "note_on";
		break;
	case note_off:
		b = "note_off";
		break;
	case control_change:
		b = "control_change";
		break;
	case pitch_wheel:
		b = "pitch_wheel";
		break;
	}

	if (evt.type == note_on || evt.type == note_off) {
		sprintf(buff, "ch: %02d %-15s %3s %3d offset: %u", evt.channel, b, i2n(evt.note), evt.velocity, evt.time);
	} else
		sprintf(buff, "ch: %02d %-15s %3d %3d offset: %u", evt.channel, b, evt.note, evt.velocity, evt.time);


	return buff;
}

char *i2n(unsigned char i) {
	static char buff[4];
	static char *notes[] = {"C-", "C#", "D-", "D#", "E-", "F-", "F#", "G-", "G#", "A-", "A#", "B-"};

	int oct = i / 12;
	int note = i%12;

	sprintf(buff, "%s%x", notes[note], oct);
	return buff;
}

void midi_buffer_clear() {
	for (int i = 0; i < JACK_CLIENT_MAX_PORTS; i++)
		curr_midi_event[i] = 0;
}

void midi_buffer_add(int port, midi_event evt) {
	if (curr_midi_event[port] == EVT_BUFFER_LENGTH)
		return;

	midi_buffer[port][curr_midi_event[port]++] = evt;

}

int midi_buffer_compare(const void *a, const void *b) {
	return ((midi_event *)a)->time - ((midi_event *)b)->time;
}

void midi_buffer_flush_port(int port) {
	void *outp = jack_port_get_buffer(jack_output_ports[port], jack_buffer_size);
	jack_midi_clear_buffer(outp);

	midi_buff_excl_in();
	for (int f = 0; f < curr_midi_queue_event[port]; f++) {
		midi_buffer_add(port, midi_queue_buffer[port][f]);
	}

	curr_midi_queue_event[port] = 0;
	midi_buff_excl_out();

	if (curr_midi_event[port] == 0)
		return;

	qsort(midi_buffer[port], curr_midi_event[port], sizeof(midi_event), midi_buffer_compare);

	for (int i = 0; i < curr_midi_event[port]; i++) {
		unsigned char buff[3];
		if (midi_encode_event(midi_buffer[port][i], buff))
			jack_midi_event_write(outp, midi_buffer[port][i].time, buff, 3);

		if (module.dump_notes) {
			char desc[256];
			midi_describe_event(midi_buffer[port][i], desc, 256);
			printf("%02d:%02d:%03d pt: %02d, %s\n", module.min, module.sec, module.ms, port, desc);
		}

	}
}

void midi_buffer_flush() {
	for (int p = 0; p < JACK_CLIENT_MAX_PORTS; p++) {
		if (jack_output_ports[p])
			midi_buffer_flush_port(p);
	}
}

int parse_note(char *buff) {
	char b[256];
	int note = 0;
	int octave = 0;

	static int notes[] = {'C', '#', 'D', '#', 'E', 'F', '#', 'G', '#', 'A', '#', 'B'};

	b[0] = 0;
	int ii = strlen(buff);
	for(int i = 0; i < ii; i++) {
		char bb[2];
		bb[0] = 0;
		bb[1] = 0;
		if (buff[i] != '-')
			bb[0] = buff[i];

		strcat(b, bb);
	}

	note = toupper(b[0]);
	int i;

	for (i = 0; (notes[i] != note) && (i < 12); i++);
	note = i;

	if (strlen(b) == 3) { // sharpie
		note++;
		octave = atoi(b + 2);
	}

	if (strlen(b) == 2) {
		octave = atoi(b + 1);
	}

	return note + octave * 12;
}

void queue_midi_note_on(sequence *seq, int port, int chn, int note, int velocity) {
	midi_event evt;
	evt.type = note_on;
	evt.channel = chn;
	evt.note = note;
	evt.velocity = velocity;
	evt.time = 0;

	if (module.recording && module.playing) {
		evt.time = jack_frame_time(jack_client) - jack_last_frame;
		if (seq)
			sequence_handle_record(seq, evt);
	}

	midi_buff_excl_in();
	midi_queue_buffer[port][curr_midi_queue_event[port]++] = evt;
	midi_buff_excl_out();
}

void queue_midi_note_off(sequence *seq, int port, int chn, int note) {
	midi_event evt;
	evt.type = note_off;
	evt.channel = chn;
	evt.note = note;
	evt.velocity = 0;
	evt.time = 0;

	if (module.recording && module.playing) {
		evt.time = jack_frame_time(jack_client) - jack_last_frame;
		if (seq)
			sequence_handle_record(seq, evt);
	}

	midi_buff_excl_in();
	midi_queue_buffer[port][curr_midi_queue_event[port]++] = evt;
	midi_buff_excl_out();
}

void midi_in_buffer_add(midi_event evt) {
	if (curr_midi_in_event == EVT_BUFFER_LENGTH)
		return;

	midi_in_buffer[curr_midi_in_event++] = evt;
}

char *midi_in_get_event() {
	if (curr_midi_in_event == 0)
		return NULL;

	midi_event evt = midi_in_buffer[--curr_midi_in_event];

	static char buff[1024];
	sprintf(buff, "{\"type\" :%d, \"note\" : %d, \"velocity\" : %d, \"time\" : %d}", evt.type, evt.note, evt.velocity, evt.time);
	return buff;
}

void midi_in_clear_events() {
	curr_midi_in_event = 0;
}
