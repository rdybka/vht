/* midi_event.h
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

#ifndef __MIDI_EVENT_H__
#define __MIDI_EVENT_H__

#include <jack/jack.h>
#include <pthread.h>
#include "jack_client.h"
#define EVT_BUFFER_LENGTH 1024

enum MIDI_EVENT_TYPE {none, note_on, note_off, pitch_wheel, control_change};
extern pthread_mutex_t midi_buff_exl; // initialised from jack_start()

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
char *midi_describe_event(midi_event evt, char *output, int len);
char *i2n(unsigned char i);
int parse_note(char *);

extern int curr_midi_event[JACK_CLIENT_MAX_PORTS];
extern int curr_midi_queue_event[JACK_CLIENT_MAX_PORTS];
void midi_buff_excl_in();
void midi_buff_excl_out();


void queue_midi_note_on(int port, int chn, int note, int velocity);
void queue_midi_note_off(int port, int chn, int note);
void midi_buffer_clear();
void midi_buffer_flush();
void midi_buffer_add(int port, midi_event evt);

#endif //__MIDI_EVENT_H__ 
