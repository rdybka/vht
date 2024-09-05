/* midi_event.c - vahatraker (libvht)
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


#include "midi_event.h"

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
	case program_change:
		buff[0] = 0xC0;
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

	char *b = "unknown";
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
	case program_change:
		b = "program_change";
		break;
	}

	if (evt.type == note_on || evt.type == note_off) {
		sprintf(buff, "ch: %02d %-15s %3s (%d) %3d offs: %u", evt.channel, b, i2n(evt.note), evt.note, evt.velocity, evt.time);
	} else
		sprintf(buff, "ch: %02d %-15s %3d %3d offs: %u", evt.channel, b, evt.note, evt.velocity, evt.time);


	return buff;
}

char *i2n(unsigned char i) {
	static char buff[4];
	static char *notes[] = {"C-", "C#", "D-", "D#", "E-", "F-", "F#", "G-", "G#", "A-", "A#", "B-"};

	int oct = i / 12;
	int note = i%12;

	if (oct > 0) {
		sprintf(buff, "%s%x", notes[note], oct - 1);
	} else {
		sprintf(buff, "%s<", notes[note]);
	}
	return buff;
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
		if (b[2] == '<')
			octave = -1;
	}

	if (strlen(b) == 2) {
		octave = atoi(b + 1);
		if (b[1] == '<')
			octave = -1;
	}


	octave++;

	while(note + octave * 12 > 127)
		octave--;

	return note + octave * 12;
}
