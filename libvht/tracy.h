/* tracy.h - vahatraker (libvht - ifrt)
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

#ifndef __TRACY_H__
#define __TRACY_H__

#include <Python.h>

#define TRACY_MAX_TAIL	32
#define TRACY_MAX_SPEED	127

typedef struct tracy_tail_coord {
	long double x, y, r;
	float dx, dy, dr;
} tail_xy;

typedef struct tracy_t {
	int type;
	// initial values
	double ix, iy, ir;

	long double x, y, r, rd;
	long double lhx, lhy; // last homed pos

	double r_sm;
	double zoom;
	double scale;
	double speed;
	double unit;
	double phase;
	double mult;
	int qnt;

	// updated each render
	float disp_x, disp_y, disp_r;
	float disp_x1, disp_y1;
	float disp_x2, disp_y2;

	tail_xy tail[TRACY_MAX_TAIL];
	int tail_length;

	int homed;
	int bailed; // trace length overkill

	pthread_mutex_t excl;
} tracy;

tracy *tracy_new(double ix, double iy, double ir);
void tracy_del(tracy *trc);
void tracy_excl_in(tracy *trc);
void tracy_excl_out(tracy *trc);
void tracy_add_tail(tracy *trc, long double x, long double y, long double r);

// public
PyObject *tracy_get_pos(tracy *trc);
PyObject *tracy_get_disp(tracy *trc);
PyObject *tracy_get_tail(tracy *trc);
double tracy_get_speed(tracy *trc);
void tracy_set_speed(tracy *trc, double s);
double tracy_get_scale(tracy *trc);
void tracy_set_scale(tracy *trc, double s);
double tracy_get_phase(tracy *trc);
void tracy_set_phase(tracy *trc, double p);
double tracy_get_mult(tracy *trc);
void tracy_set_mult(tracy *trc, double m);
int tracy_get_amode(tracy *trc);
void tracy_set_amode(tracy *trc, int m);
int tracy_get_qnt(tracy *trc);
void tracy_set_qnt(tracy *trc, int q);
double tracy_get_zoom(tracy *trc);
void tracy_set_zoom(tracy *trc, double z);
#endif //__TRACY_H__
