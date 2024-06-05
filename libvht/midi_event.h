/* midi_event.h - vahatraker (libvht)
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

#ifndef __MIDI_EVENT_H__
#define __MIDI_EVENT_H__

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <jack/jack.h>

enum MIDI_EVENT_TYPE {none, note_on, note_off, pitch_wheel, control_change, program_change};

typedef struct midi_event_t {
	jack_nframes_t time;
	int type;
	unsigned char channel;
	union {
		unsigned char note;
		unsigned char control;
		unsigned char lsb;
	};
	union {
		unsigned char velocity;
		unsigned char data;
		unsigned char msb;
	};
} midi_event;

midi_event midi_decode_event(unsigned char *data, int len);
int midi_encode_event(midi_event evt, unsigned char *buff);

char *midi_describe_event(midi_event evt, char *output, int len);
char *i2n(unsigned char i);
int parse_note(char *);

#endif //__MIDI_EVENT_H__ 
