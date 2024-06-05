/* ctrlrow.h - vahatraker (libvht)
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

#ifndef __CTRLROW_H__
#define __CTRLROW_H__

typedef struct ctrlrow_t {
	int velocity;
	int linked;
	int smooth;		// 0 - sharp, 9 - smooth
	int anchor;		// 0 - top, 1 - bottom
} ctrlrow;

int ctrlrow_get_velocity(ctrlrow *crw);
int ctrlrow_get_linked(ctrlrow *crw);
int ctrlrow_get_smooth(ctrlrow *crw);
int ctrlrow_get_anchor(ctrlrow *crw);

void ctrlrow_set_velocity(ctrlrow *crw, int velocity);
void ctrlrow_set_linked(ctrlrow *crw, int linked);
void ctrlrow_set_smooth(ctrlrow *crw, int smooth);
void ctrlrow_set_anchor(ctrlrow *crw, int anchor);

void ctrlrow_set(ctrlrow *crw, int velocity, int linked, int smooth, int anchor);

#endif //__CTRLROW_H__
