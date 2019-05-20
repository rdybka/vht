/* row.c - Valhalla Tracker (libvht)
 *
 * Copyright (C) 2019 Remigiusz Dybka - remigiusz.dybka@gmail.com
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

#include "row.h"

int row_get_type(row *rw) {
	return rw->type;
}

int row_get_note(row *rw) {
	return rw->note;
}

int row_get_velocity(row *rw) {
	return rw->velocity;
}

int row_get_delay(row *rw) {
	return rw->delay;
}

void row_set_type(row *rw, int type) {
	rw->type = type;
}

void row_set_note(row *rw, int note) {
	rw->note = note;
}

void row_set_velocity(row *rw, int velocity) {
	rw->velocity = velocity;
}

void row_set_delay(row *rw, int delay) {
	rw->delay = delay;
}

void row_set(row *rw, int type, int note, int velocity, int delay) {
	rw->type = type;
	rw->note = note;
	rw->velocity = velocity;
	rw->delay = delay;
}
