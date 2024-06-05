/* tracy.c - vahatraker (libvht)
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

#include "tracy.h"

void tracy_excl_in(tracy *trc) {
	pthread_mutex_lock(&trc->excl);
}

void tracy_excl_out(tracy *trc) {
	pthread_mutex_unlock(&trc->excl);
}

tracy *tracy_new(double ix, double iy, double ir) {
	tracy *trc = malloc(sizeof(tracy));
	trc->ix = ix;
	trc->iy = iy;
	trc->ir = ir;

	trc->x = ix;
	trc->y = iy;
	trc->lhx = 0;
	trc->lhy = 0;
	trc->r = ir;
	trc->rd = ir;

	trc->zoom = 3;
	trc->scale = 1;
	trc->speed = 5;
	trc->unit = 1;
	trc->r_sm = .5;
	trc->tail_length = 0;
	trc->phase = 0;
	trc->mult = 1;
	trc->qnt = 0;

	trc->homed = 0;
	trc->bailed = 0;
	trc->type = 0;
	pthread_mutex_init(&trc->excl, NULL);
	return trc;
}

void tracy_del(tracy *trc) {
	pthread_mutex_destroy(&trc->excl);
	free(trc);
}

void tracy_set_init(tracy *trc, double ix, double iy, double ir) {
	tracy_excl_in(trc);
	trc->ix = ix;
	trc->iy = iy;
	trc->ir = ir;

	trc->rd = ir;
	trc->x = ix;
	trc->y = iy;
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
	PyDict_SetItemString(r, "ix", PyFloat_FromDouble(trc->ix));
	PyDict_SetItemString(r, "iy", PyFloat_FromDouble(trc->iy));
	PyDict_SetItemString(r, "ir", PyFloat_FromDouble(trc->ir));
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
	trc->bailed = 0;
	tracy_excl_out(trc);
	return r;
}

double tracy_get_speed(tracy *trc) {
	return trc->speed;
}
void tracy_set_speed(tracy *trc, double s) {
	tracy_excl_in(trc);
	int swp = 0;

	if (s < 0) {
		swp = 1;
		s *= -1;
	}

	if (s < .1)
		s = .1;

	if (s > TRACY_MAX_SPEED)
		s = TRACY_MAX_SPEED;

	if (swp) {
		s *= -1;
	}

	trc->speed = s;
	tracy_excl_out(trc);
}

double tracy_get_scale(tracy *trc) {
	return trc->scale;
}
void tracy_set_scale(tracy *trc, double s) {
	trc->scale = s;
}

double tracy_get_phase(tracy *trc) {
	return trc->phase * 180 / M_PI;
}

void tracy_set_phase(tracy *trc, double p) {
	trc->phase = p * M_PI / 180;
}

double tracy_get_mult(tracy *trc) {
	return trc->mult;
}

void tracy_set_mult(tracy *trc, double m) {
	trc->mult = m;
}

int tracy_get_qnt(tracy *trc) {
	return trc->qnt;
}

void tracy_set_qnt(tracy *trc, int q) {
	trc->qnt = q;
}

double tracy_get_zoom(tracy *trc) {
	return trc->zoom;
}

void tracy_set_zoom(tracy *trc, double z) {
	trc->zoom = z;
}
