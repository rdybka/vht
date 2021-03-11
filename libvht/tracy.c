/* tracy.c - Valhalla Tracker (libvht)
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

#include "tracy.h"

void tracy_excl_in(tracy *trc) {
	pthread_mutex_lock(&trc->excl);
}

void tracy_excl_out(tracy *trc) {
	pthread_mutex_unlock(&trc->excl);
}

tracy *tracy_new(double ix1, double iy1, double ix2, double iy2) {
	tracy *trc = malloc(sizeof(tracy));
	trc->ix1 = ix1;
	trc->iy1 = iy1;
	trc->ix2 = ix2;
	trc->iy2 = iy2;

	trc->x = 0;
	trc->y = 0;
	trc->lhx = 0;
	trc->lhy = 0;
	trc->r = 0;
	trc->rd = 0;

	trc->zoom = 1;
	trc->speed = .1;
	trc->r_sm = .2;
	trc->tail_length = 0;

	trc->homed = 0;
	trc->bailed = 0;

	pthread_mutex_init(&trc->excl, NULL);
	return trc;
}

void tracy_del(tracy *trc) {
	pthread_mutex_destroy(&trc->excl);
	free(trc);
}

void tracy_set_init(tracy *trc, double ix1, double iy1, double ix2, double iy2) {
	tracy_excl_in(trc);
	trc->ix1 = ix1;
	trc->iy1 = iy1;
	trc->ix2 = ix2;
	trc->iy2 = iy2;
	tracy_excl_out(trc);
}

void tracy_add_tail(tracy *trc, long double x, long double y, long double r) {
	trc->tail_length++;
	if (trc->tail_length >= TRACY_MAX_TAIL)
		trc->tail_length = TRACY_MAX_TAIL - 1;

	for (int t = TRACY_MAX_TAIL - 1; t > 0; t--) {
		trc->tail[t] = trc->tail[t - 1];
	}

	trc->tail[0].x = x;
	trc->tail[0].y = y;
	trc->tail[0].r = r;
}

PyObject *tracy_get_tail(tracy *trc) {
	PyObject *ret = PyList_New(0);
	for (int t = 0; t < trc->tail_length; t++) {
		PyObject *x = PyFloat_FromDouble(trc->tail[t].dx);
		PyObject *y = PyFloat_FromDouble(trc->tail[t].dy);
		PyObject *r = PyFloat_FromDouble(trc->tail[t].dr);
		PyObject *tpl = PyTuple_Pack(3, x, y, r);
		PyList_Append(ret, tpl);
	}
	return ret;
}

PyObject *tracy_get_init(tracy *trc) {
	tracy_excl_in(trc);
	PyObject *r = PyDict_New();
	PyDict_SetItemString(r, "ix1", PyFloat_FromDouble(trc->ix1));
	PyDict_SetItemString(r, "iy1", PyFloat_FromDouble(trc->iy1));
	PyDict_SetItemString(r, "ix2", PyFloat_FromDouble(trc->ix2));
	PyDict_SetItemString(r, "iy2", PyFloat_FromDouble(trc->iy2));
	tracy_excl_out(trc);
	return r;
}

PyObject *tracy_get_pos(tracy *trc) {
	tracy_excl_in(trc);
	PyObject *r = PyDict_New();
	PyDict_SetItemString(r, "x", PyFloat_FromDouble(trc->x));
	PyDict_SetItemString(r, "y", PyFloat_FromDouble(trc->y));
	PyDict_SetItemString(r, "r", PyFloat_FromDouble(trc->rd));
	tracy_excl_out(trc);
	return r;
}

PyObject *tracy_get_disp(tracy *trc) {
	tracy_excl_in(trc);
	PyObject *r = PyDict_New();
	PyDict_SetItemString(r, "x", PyFloat_FromDouble(trc->disp_x));
	PyDict_SetItemString(r, "y", PyFloat_FromDouble(trc->disp_y));
	PyDict_SetItemString(r, "r", PyFloat_FromDouble(trc->disp_r));
	PyDict_SetItemString(r, "zoom", PyFloat_FromDouble(trc->zoom));
	PyDict_SetItemString(r, "bailed", PyLong_FromLong(trc->bailed));
	PyDict_SetItemString(r, "x1", PyFloat_FromDouble(trc->disp_x1));
	PyDict_SetItemString(r, "y1", PyFloat_FromDouble(trc->disp_y1));
	PyDict_SetItemString(r, "x2", PyFloat_FromDouble(trc->disp_x2));
	PyDict_SetItemString(r, "y2", PyFloat_FromDouble(trc->disp_y2));
	tracy_excl_out(trc);
	return r;
}

