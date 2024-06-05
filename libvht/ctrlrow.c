/* ctrlrow.c - vahatraker (libvht)
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

#include "ctrlrow.h"

int ctrlrow_get_velocity(ctrlrow *crw) {
	return crw->velocity;
}

int ctrlrow_get_linked(ctrlrow *crw) {
	return crw->linked;
}

int ctrlrow_get_smooth(ctrlrow *crw) {
	return crw->smooth;
}

int ctrlrow_get_anchor(ctrlrow *crw) {
	return crw->anchor;
}


void ctrlrow_set_velocity(ctrlrow *crw, int velocity) {
	crw->velocity = velocity;
}

void ctrlrow_set_linked(ctrlrow *crw, int linked) {
	crw->linked = linked;
}

void ctrlrow_set_smooth(ctrlrow *crw, int smooth) {
	crw->smooth = smooth;
}

void ctrlrow_set_anchor(ctrlrow *crw, int anchor) {
	crw->anchor = anchor;
}

void ctrlrow_set(ctrlrow *crw, int velocity, int linked, int smooth, int anchor) {
	crw->velocity = velocity;
	crw->linked = linked;
	crw->smooth = smooth;
	crw->anchor = anchor;
}
