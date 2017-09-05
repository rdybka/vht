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

#include "midi_event.h"

midi_event midi_decode_event(unsigned char *data, int len) {
    midi_event ret;
    ret.type = unknown;

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

    return ret;
}

char * midi_describe_event(midi_event  evt, char *buff, int len) {
    buff[0] = 0;

    char *b;
    switch(evt.type) {
    case unknown:
        b = "unknown";
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
        sprintf(buff, "ch: %02d %-15s %3s %d", evt.channel, b, i2n(evt.note), evt.velocity);
    } else
        sprintf(buff, "ch: %02d %-15s %d %d", evt.channel, b, evt.note, evt.velocity);


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
