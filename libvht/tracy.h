/* tracy.h - Valhalla Tracker (libvht)
 *
 * Copyright (C) 2021 Remigiusz Dybka - remigiusz.dybka@gmail.com
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

#ifndef __TRACY_H__
#define __TRACY_H__

#include <Python.h>

enum tracy_type {two_point, turtle};

typedef struct tracy_t {
	int type;
	// initial values
	double ix1, iy1, ix2, iy2;

	long double x, y, r, rd;
	long double lhx, lhy; // last homed pos

	double r_sm;
	double zoom;
	double speed;
	double unit;

	// updated each render
	float disp_x, disp_y, disp_r;
	float disp_x1, disp_y1;
	float disp_x2, disp_y2;

	int homed;
	int bailed; // trace length overkill

	pthread_mutex_t excl;
} tracy;

tracy *tracy_new(double ix1, double iy1, double ix2, double iy2);
void tracy_del(tracy *trc);
void tracy_excl_in(tracy *trc);
void tracy_excl_out(tracy *trc);

// public
void tracy_set_init(tracy *trc, double ix1, double iy1, double ix2, double iy2);
PyObject *tracy_get_init(tracy *trc);
PyObject *tracy_get_pos(tracy *trc);
PyObject *tracy_get_disp(tracy *trc);

#endif //__TRACY_H__
