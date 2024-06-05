/* mandy.c - vahatraker (libvht)
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

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <Python.h>
#include "midi_client.h"
#include "track.h"
#include "mandy_trk_disp.h"
#include "mandy_pix_scan.h"

void mandy_excl_in(mandy *mand) {
	pthread_mutex_lock(&mand->excl);
}

void mandy_excl_out(mandy *mand) {
	pthread_mutex_unlock(&mand->excl);
}

void mandy_excl_vect_in(mandy *mand) {
	pthread_mutex_lock(&mand->excl_vect);
}

void mandy_excl_vect_out(mandy *mand) {
	pthread_mutex_unlock(&mand->excl_vect);
}

mandy *mandy_new(void *vtrk) {
	mandy *mand = malloc(sizeof(mandy));
	mand->trk = vtrk;

	pthread_mutex_init(&mand->excl, NULL);
	pthread_mutex_init(&mand->excl_vect, NULL);
	track *trk = (track *)mand->trk;
	trk->mand = mand;
	mand->info = NULL;
	mand->fr = 255;
	mand->fg = 255;
	mand->fb = 255;
	mand->px =-23;
	mand->py =-23;
	mand->active = 0;
	mand->pause = 0;
	mand->step = 0;
	mand->vect = NULL;
	mand->nvect = 0;
	mand->navect = 0;

	mand->tracies = NULL;
	mand->ntracies = 0;
	mand->follow = -1;
	mand->julia = 1;

	mand->unit0 = 1.0 / pow(2.0, 52);

	mand->pixmap = NULL;
	mand->last_res_x = 0;
	mand->last_res_y = 0;
	mand->last_stride = 0;
	mand->last_rend_res = MANDY_REND_RES;
	mand->last_rend_sq = 0;
	mand->render = 0;

	mand->pix_mask = NULL;

	mand->scan_trc = tracy_new(.23, 0, 0);
	mand->init_trc = tracy_new(.23, 0, 0);

	mand->miter = MANDY_DEF_MITER;
	mand->bail = MANDY_DEF_BAIL;

	mand->x = -.7;
	mand->dx = mand->x;
	mand->y = 0;
	mand->dy = mand->y;

	mand->jcx = 0.0;
	mand->jcy = 0.0;
	mand->jvx = 0.0;
	mand->jvy = 0.0;
	mand->jsx = 0.0;
	mand->jsy = 0.0;
	mand->jrx = 0.0;
	mand->jry = 0.0;
	mand->jx = 0.0;
	mand->jy = 0.0;

	mand->zoom = 6.0;
	mand->dzoom = mand->zoom;
	mand->rot = 0.0;
	mand->drot = mand->rot;

	mand->fps = 0;
	mand->last_t = 0;
	mand->nframes = 0;

	mand->mn = 2.23;
	mand->mubrot = 0;	// maybe one day
	mandy_set_display(mand, 32, 32, 32);
	mandy_reset(mand);
	return mand;
}

void mandy_free(mandy *mand) {
	track *trk = (track *)mand->trk;
	trk->mand = NULL;
	free(mand->pixmap);
	free(mand->vect);
	for (unsigned int t = 0; t < mand->ntracies; t++) {
		tracy_del(mand->tracies[t]);
	}
	free(mand->tracies);
	tracy_del(mand->scan_trc);
	tracy_del(mand->init_trc);
	free(mand->pix_mask);
	pthread_mutex_destroy(&mand->excl);
	pthread_mutex_destroy(&mand->excl_vect);
	free(mand);
}

double rad2deg(double r) {
	double deg = r * (180.0 / M_PI);
	while(deg < -180.0)
		deg += 360.0;

	while(deg > 180.0)
		deg -= 360.0;

	return deg;
}

void rotate(long double cx, long double cy, long double r, long double *x, long double *y) {
	long double rr = 0;
	long double l = sqrt(pow((*y - cy), 2) + pow((*x - cx), 2));
	r -= HALFPI;

	rr = atan2((*x - cx), (*y - cy));
	rr += r;

	*x = cx + l * cos(rr);
	*y = cy + l * sin(rr);
}

// disp to fractal
void mandy_d2f(mandy *mand, float x, float y, long double *fx, long double *fy) {
	*fx = mand->x1 + (mand->delta_xx * x) + (mand->delta_xy * y);
	*fy = mand->y1 + (mand->delta_yy * y) + (mand->delta_yx * x);
}

// fract to disp
void mandy_f2d(mandy *mand, float *x, float *y, long double fx, long double fy) {
	long double nx = fx;
	long double ny = fy;
	rotate(mand->x, mand->y, mand->rot, &nx, &ny);
	*x = (float)(nx - mand->x0) / mand->delta_x;
	*y = (float)(ny - mand->y0) / mand->delta_y;
}


void mandy_translate(mandy *mand, float x, float y, float w, float h) {
	long double dx = (x / w * mand->zoom);
	long double dy = (y / w * mand->zoom); // not a typo :]

	rotate(0, 0, mand->rot, &dx, &dy);
	mand->dx -= dx;
	mand->dy -= dy;
	mand->render = 1;
}

void mandy_update_julia(mandy *mand) {
	long double unit = 0.1 / pow(MAGIC_MITER2UNIT_RATIO, mand->miter);
	double vx = unit * pow(2, mand->jvx);
	double vy = unit * pow(2, mand->jvy);

	mand->jx = mand->jcx + vx * cos(mand->jrx);
	mand->jy = mand->jcy + vy * cos(mand->jry);
	mand->render = 1;
}

void mandy_translate_julia(mandy *mand, float x, float y, float w, float h) {
	long double dx = (x / w * mand->zoom);
	long double dy = (y / w * mand->zoom);

	mandy_excl_in(mand);

	rotate(0, 0, mand->rot, &dx, &dy);
	mand->jcx -= dx;
	mand->jcy -= dy;

	mandy_update_julia(mand);
	mand->init_trc->unit = 0.1 / pow(MAGIC_MITER2UNIT_RATIO, mand->miter);
	mandy_trc_home(mand, mand->init_trc);
	//mandy_f2d(mand, &mand->init_trc->disp_x, &mand->init_trc->disp_y, mand->init_trc->x, mand->init_trc->y);
	//mand->init_trc->disp_r = mand->rot - mand->init_trc->rd;
	mandy_excl_out(mand);
}

void mandy_rotate(mandy *mand, float x, float y, float w, float h) {
	mand->drot += x / w * M_PI;
	mand->render = 1;
}

void mandy_zoom(mandy *mand, float x, float y, float w, float h) {
	double mlt = 1.01;
	int n = abs(ceil(y));
	mand->render = 1;

	if (mand->follow > -1) {
		tracy *trc = mand->tracies[mand->follow];

		for (int f = 0; f < n; f++) {
			if (y < 0) {
				trc->zoom /= mlt;
			} else {
				trc->zoom *= mlt;
			}

			if (trc->zoom < .02)
				trc->zoom = .02;
		}

		return;
	} else {
		for (unsigned int t = 0; t < mand->ntracies; t++) {
			mand->tracies[t]->zoom = 1.0;
		}
	}

	for (int f = 0; f < n; f++) {
		if (y < 0) {
			mand->dzoom /= mlt;
		} else {
			mand->dzoom *= mlt;
		}
	}
}

mandy *mandy_clone(mandy *mand, void *vtrk) {
	if (!mand)
		return NULL;

	PyObject *s = mandy_save(mand);

	mandy *nmand = mandy_new(vtrk);
	mandy_restore(nmand, s);

	Py_DECREF(s);
	return nmand;
}

void mandy_gen_info(mandy *mand) {
	char inf[256];
	if (!mand->ntracies) {
		sprintf(inf, "fps: %d niter: %d\nzoom: %.7Lf\nx, y, r = [%.7Lf, %.7Lf, %.3f]\njcx, jcy = [%.7Lf, %.7Lf]\njx, jy = [%.7Lf, %.7Lf]", \
		        mand->fps, mand->miter, mand->zoom, mand->x, mand->y, rad2deg(mand->rot), mand->jcx, mand->jcy, mand->jx, mand->jy);
	} else {
		sprintf(inf, "fps: %d niter: %d\nzoom: %.7Lf\nx, y, r = [%.7Lf, %.7Lf, %.3f]\ntrc x, y, r = [%.7Lf, %.7Lf, %.3f]\njcx, jcy = [%.7Lf, %.7Lf]\njx, jy = [%.7Lf, %.7Lf]", \
		        mand->fps, mand->miter, mand->zoom, mand->x, mand->y, rad2deg(mand->rot), mand->tracies[0]->x, mand->tracies[0]->y, rad2deg(mand->tracies[0]->r), mand->jcx, mand->jcy, mand->jx, mand->jy);
	}

	mandy_set_info(mand, inf);
}

void mandy_reset(mandy *mand) {
	mandy_excl_in(mand);

	mand->jrx = 0;
	mand->jry = 0;
	mandy_update_julia(mand);
	mand->init_trc->unit = 0.1 / pow(MAGIC_MITER2UNIT_RATIO, mand->miter);

	mandy_trc_home(mand, mand->init_trc);

	if (mand->follow > -1) {
		mand->rot = mand->init_trc->rd;
		mand->drot = mand->init_trc->rd;
	}

	if (mand->ntracies) {
		mand->tracies[0]->x = mand->init_trc->x;
		mand->tracies[0]->y = mand->init_trc->y;
		mand->tracies[0]->r = mand->init_trc->rd;
		mand->tracies[0]->rd = mand->init_trc->rd;
		mand->tracies[0]->unit = mand->init_trc->unit;
	}

	mandy_excl_out(mand);

	if (mand->pause) {
		if (mand->ntracies)
			mand->tracies[0]->tail_length = 0;
	}

	mandy_advance(mand, 0, 0);

	if (mand->active) {
		track *trk = (track *)mand->trk;
		trk->last_pos = 0;
	}

	mandy_gen_info(mand);
}

void mandy_reset_anim(mandy *mand) {
	if (mand->follow > -1) {
		mand->drot = mand->tracies[mand->follow]->r - HALFPI;
		mand->rot = mand->drot;
	}

	if (mand->ntracies) {
		mand->tracies[0]->tail_length = 0;
	}
}

int getint(PyObject *o, const char *k) {
	PyObject *itm = PyDict_GetItemString(o, k);
	if (!itm) {
		printf("%s not found!\n", k);
		return 0;
	}

	if (PyLong_Check(itm)) {
		return PyLong_AsLong(itm);
	} else {
		printf("%s not long\n", k);
		return 0;
	}
}

double getdouble(PyObject *o, const char *k) {
	PyObject *itm = PyDict_GetItemString(o, k);
	if (!itm) {
		printf("%s not found!\n", k);
		return 0;
	}

	if (PyFloat_Check(itm)) {
		return PyFloat_AsDouble(itm);
	} else {
		printf("%s not float\n", k);
		return 0;
	}
}

tracy *mandy_add_tracy(mandy *mand, double x, double y, double r) {
	tracy *trc = tracy_new(x, y, r);

	trc->unit = 0.1 / pow(MAGIC_MITER2UNIT_RATIO, mand->miter);
	trc->homed = 0;
	mand->tracies = realloc(mand->tracies, sizeof (tracy *) * mand->ntracies + 1);

	mand->tracies[mand->ntracies++] = trc;

	mandy_trc_home(mand, trc);
	trc->r = trc->rd;
	return trc;
}

void mandy_restore(mandy *mand, PyObject *o) {
	mandy_excl_in(mand);

	mand->active = getint(o, "active");
	mand->miter = getint(o, "miter");
	if (!mand->miter) {
		mand->miter = MANDY_DEF_MITER;
	}

	mand->pause = getint(o, "pause");
	mand->julia = getint(o, "julia");

	mand->x = getdouble(o, "x");
	mand->dx = mand->x;
	mand->y = getdouble(o, "y");
	mand->dy = mand->y;
	mand->rot = getdouble(o, "r");
	mand->drot = mand->rot;
	mand->zoom = getdouble(o, "z");
	mand->dzoom = mand->zoom;

	mand->jcx = getdouble(o, "jcx");
	mand->jcy = getdouble(o, "jcy");
	mand->jvx = getdouble(o, "jvx");
	mand->jvy = getdouble(o, "jvy");
	mand->jsx = getdouble(o, "jsx");
	mand->jsy = getdouble(o, "jsy");
	mand->jrx = getdouble(o, "jrx");
	mand->jry = getdouble(o, "jry");

	mandy_update_julia(mand);

	PyObject *t = PyDict_GetItemString(o, "init_trc");
	if (t) {
		mand->init_trc->x = getdouble(t, "x");
		mand->init_trc->y = getdouble(t, "y");
		mand->init_trc->r = getdouble(t, "r");
		mand->init_trc->rd = mand->init_trc->r;
		mand->init_trc->unit = 0.1 / pow(MAGIC_MITER2UNIT_RATIO, mand->miter);
		mandy_trc_home(mand, mand->init_trc);
	}

	PyObject *p = PyDict_GetItemString(o, "trc_pos");

	if (p && !mand->ntracies) {
		mandy_add_tracy(mand, mand->init_trc->x, mand->init_trc->y, mand->init_trc->r);

		mand->tracies[0]->zoom = getdouble(o, "trc_zoom");
		mand->tracies[0]->speed = getdouble(o, "trc_speed");
		mand->tracies[0]->unit = getdouble(o, "trc_unit");
		mand->tracies[0]->phase = getdouble(o, "trc_phase");
		mand->tracies[0]->mult = getdouble(o, "trc_mult");
		mand->tracies[0]->type = getint(o, "trc_type");
		mand->tracies[0]->qnt = getint(o, "trc_qnt");
		mand->tracies[0]->scale = fmax(1, getdouble(o, "trc_scl"));

		mandy_trc_home(mand, mand->tracies[0]);
	}

	PyObject *f = PyDict_GetItemString(o, "follow");
	mand->follow = -1;
	if (f) {
		mand->follow = PyLong_AsLong(f);
	}

	mandy_excl_out(mand);
}

PyObject *mandy_save(mandy *mand) {
	PyObject *r = PyDict_New();

	mandy_excl_in(mand);
	PyDict_SetItemString(r, "active", PyLong_FromLong(mand->active));
	PyDict_SetItemString(r, "pause", PyLong_FromLong(mand->pause));
	PyDict_SetItemString(r, "miter", PyLong_FromLong(mand->miter));
	PyDict_SetItemString(r, "julia", PyLong_FromLong(mand->julia));
	PyDict_SetItemString(r, "follow", PyLong_FromLong(mand->follow));
	PyDict_SetItemString(r, "x", PyFloat_FromDouble(mand->dx));
	PyDict_SetItemString(r, "y", PyFloat_FromDouble(mand->dy));
	PyDict_SetItemString(r, "r", PyFloat_FromDouble(mand->drot));
	PyDict_SetItemString(r, "z", PyFloat_FromDouble(mand->dzoom));
	PyDict_SetItemString(r, "jcx", PyFloat_FromDouble(mand->jcx));
	PyDict_SetItemString(r, "jcy", PyFloat_FromDouble(mand->jcy));
	PyDict_SetItemString(r, "jvx", PyFloat_FromDouble(mand->jvx));
	PyDict_SetItemString(r, "jvy", PyFloat_FromDouble(mand->jvy));
	PyDict_SetItemString(r, "jsx", PyFloat_FromDouble(mand->jsx));
	PyDict_SetItemString(r, "jsy", PyFloat_FromDouble(mand->jsy));
	PyDict_SetItemString(r, "jrx", PyFloat_FromDouble(mand->jrx));
	PyDict_SetItemString(r, "jry", PyFloat_FromDouble(mand->jry));

	PyDict_SetItemString(r, "init_trc", tracy_get_pos(mand->init_trc));
	if (mand->ntracies) {
		PyDict_SetItemString(r, "trc_pos", tracy_get_pos(mand->tracies[0]));
		PyDict_SetItemString(r, "trc_zoom", PyFloat_FromDouble(mand->tracies[0]->zoom));
		PyDict_SetItemString(r, "trc_speed", PyFloat_FromDouble(mand->tracies[0]->speed));
		PyDict_SetItemString(r, "trc_unit", PyFloat_FromDouble(mand->tracies[0]->unit));
		PyDict_SetItemString(r, "trc_phase", PyFloat_FromDouble(mand->tracies[0]->phase));
		PyDict_SetItemString(r, "trc_mult", PyFloat_FromDouble(mand->tracies[0]->mult));
		PyDict_SetItemString(r, "trc_type", PyLong_FromLong(mand->tracies[0]->type));
		PyDict_SetItemString(r, "trc_qnt", PyLong_FromLong(mand->tracies[0]->qnt));
		PyDict_SetItemString(r, "trc_scl", PyFloat_FromDouble(mand->tracies[0]->scale));
	}

	mandy_excl_out(mand);

	return r;
}

// this runs in jack thread
void mandy_advance(mandy *mand, double tperiod, jack_nframes_t nframes) {
	if (!mand)
		return;

	mandy_excl_in(mand);

	track *trk = (track *)mand->trk;

	if (mand->pause && !mand->step) {
		mandy_excl_out(mand);
		mandy_gen_info(mand);
		return;
	}

	mand->step = 0;

	mand->jrx += (tperiod / 16) * mand->jsx;
	mand->jry += (tperiod / 16) * mand->jsy;

	mandy_update_julia(mand);
	mandy_excl_out(mand);

	// update tracies
	for (unsigned int t = 0; t < mand->ntracies; t++) {
		tracy *trc = mand->tracies[t];
		tracy_excl_in(trc);

		long double nunit = 0.1 / pow(MAGIC_MITER2UNIT_RATIO, mand->miter);
		nunit *= pow(2, trc->scale);
		trc->unit = nunit;//fmin(fmax(trc->unit, nunit), nunit * 4);

		mandy_trc_move(mand, trc, tperiod);
		trc->r += atan2(sin(trc->rd - trc->r), cos(trc->rd - trc->r)) * trc->r_sm;

		trk->pos = (-trc->phase + (-trc->r * trc->mult)) / (M_PI * 2.0) * trk->nrows;

		while(trk->pos > trk->nrows)
			trk->pos -= trk->nrows;

		while(trk->pos < 0)
			trk->pos += trk->nrows;

		tracy_excl_out(trc);
	}
	mandy_gen_info(mand);
}

// this runs in gui thread
void mandy_animate(mandy *mand) {
	double sm = 1.5;

	long double dx = mand->dx;
	long double dy = mand->dy;
	long double drot = mand->drot;
	long double dzoom = mand->dzoom;

	/*for (unsigned int tr = 0; tr < mand->ntracies; tr++) {
		tracy *trc = mand->tracies[tr];
		for (int t = 0; t < trc->tail_length; t++) {
			trc->tail[t].x = trc->tail[t].x + (trc->unit / 100) * cos(trc->tail[t].r);
			trc->tail[t].y = trc->tail[t].y + (trc->unit / 100) * sin(trc->tail[t].r);
			trc->tail[t].r *= 1.01;
		}
	}
	*/
	if (mand->follow > -1) {
		mand->dx = mand->tracies[mand->follow]->x;
		mand->dy = mand->tracies[mand->follow]->y;

		mand->dzoom = mand->tracies[mand->follow]->zoom * mand->tracies[mand->follow]->unit * 10;
		mand->drot = mand->tracies[mand->follow]->r - HALFPI;

		mand->x += (mand->dx - mand->x) / sm;
		mand->y += (mand->dy - mand->y) / sm;

		mand->rot += (mand->drot - mand->rot) / (sm * 5);
		mand->zoom += (mand->dzoom - mand->zoom) / (sm * 5);

		mand->render = 1;
	} else {
		mand->x = dx;
		mand->y = dy;
		mand->rot = drot;
		mand->zoom = dzoom;
	}
}

// the algo
unsigned char mandy_v(mandy *mand, long double x, long double y) {
	long double xx = mand->jx;
	long double yy = mand->jy;
	long double nx = 0.0;
	long double ny = 0.0;
	long double sx = x;
	long double sy = y;
	unsigned char v = 0;

	if (mand->julia) {
		xx = x;
		yy = y;
		sx = mand->jx;
		sy = mand->jy;
	}

	for (int f = 0; f < mand->miter; f++) {
		// too expensive (for now?)
		/*if (mand->mubrot) {
			nx = pow(xx*xx+yy*yy, mand->mn/2)*cos(mand->mn*atan2(yy,xx)) + sx;
			ny = pow(xx*xx+yy*yy, mand->mn/2)*sin(mand->mn*atan2(yy,xx)) + sy;
		} else { */
		nx = xx*xx - yy*yy + sx;
		ny = 2.0*xx*yy + sy;
		//}

		if ((nx*nx+ny*ny) > mand->bail) {
			break;
		}

		v = f;

		xx = nx;
		yy = ny;
	}

	v++;

	if (v == mand->miter)
		v = 0;

	return v;
}

// the god function
long double mandy_isect(mandy *mand,\
                        long double x1, long double y1,\
                        long double x2, long double y2,\
                        long double unit,\
                        long double *ix, long double *iy,\
                        int norot) { // omit rotation

	unsigned char p1 = mandy_v(mand, x1, y1);
	unsigned char p2 = mandy_v(mand, x2, y2);

	if (p1 > 0 && p2 > 0) { // both out
		return -23;
	}

	if (p1 == 0 && p2 == 0) { // both in
		return -23;
	}

	if (p1 > 0 && p2 == 0) { // need swapping
		long double xx = x2;
		x2 = x1;
		x1 = xx;

		long double yy = y2;
		y2 = y1;
		y1 = yy;

		unsigned char pp = p2;
		p2 = p1;
		p1 = pp;
	}

	// get the point between
	long double x3 = (x1 + x2) / 2.0;
	long double y3 = (y1 + y2) / 2.0;
	unsigned char p3 = mandy_v(mand, x3, y3);

	if (p3 == 0) { // inside
		x1 = x3;
		y1 = y3;
	} else {
		x2 = x3;
		y2 = y3;
	}

	*ix = x3;
	*iy = y3;

	long double lx = fabs(x2 - x1);
	long double ly = fabs(y2 - y1);

	if (sqrt(pow(lx, 2) + pow(ly, 2)) > unit) {
		return mandy_isect(mand, x1, y1, x2, y2, unit, ix, iy, norot);
	}

	if (norot) {
		return(-22);
	}

	unit /= 9.69420;
	mandy_isect(mand, x1, y1, x2, y2, unit, ix, iy, 1);
	x3 = *ix;
	y3 = *iy;

	int div = 6;	// that's how I like it, with pineapple and jalapenos

	long double r0 = 0.0;

	double rr = (M_PI * 2) / div;
	int been_out = 0;

	for (int d = 0; d < div * 2 && been_out != 2; d++) {
		double r = rr * d;

		double lx1 = x3 + unit * 100 * cos(r);
		double ly1 = y3 + unit * 100 * sin(r);
		double lx2 = x3 + unit * 100 * cos(r - rr);
		double ly2 = y3 + unit * 100 * sin(r - rr);

		long double lix = 0;
		long double liy = 0;

		unsigned char p3 = mandy_v(mand, lx1, ly1);
		if (!p3 && been_out == 1) {
			mandy_isect(mand, lx1, ly1, lx2, ly2, unit, &lix, &liy, 1);
			r0 = atan2((liy - y3), (lix - x3));
			been_out = 2;
		} else {
			if (p3 && been_out != 2) {
				been_out = 1;
			}
		}
	}

	return r0;
}

void mandy_set_display(mandy *mand, int width, int height, int stride) {
	double dw = (double)width;
	double dh = (double)height;

	double rat = dh / dw;

	long double x1 = mand->x - ((dw / 2.0) / dw) * mand->zoom;
	long double y1 = mand->y - ((dh / 2.0) / dh) * mand->zoom * rat;

	long double x2 = mand->x + ((dw / 2.0) / dw) * mand->zoom;
	long double y2 = mand->y - ((dh / 2.0) / dh) * mand->zoom * rat;

	long double x4 = mand->x - ((dw / 2.0) / dw) * mand->zoom;
	long double y4 = mand->y + ((dh / 2.0) / dh) * mand->zoom * rat;

	// save for f2d
	mand->x0 = x1;
	mand->y0 = y1;
	mand->delta_x = (x2 - x1) / dw;
	mand->delta_y = (y4 - y1) / dh;

	// rotate around x, y
	rotate(mand->x, mand->y, mand->rot, &x1, &y1);
	rotate(mand->x, mand->y, mand->rot, &x2, &y2);
	rotate(mand->x, mand->y, mand->rot, &x4, &y4);

	mand->x1 = x1;
	mand->y1 = y1;

	mand->delta_xx = (x2 - x1) / dw;
	mand->delta_xy = (y2 - y1) / dw;
	mand->delta_yx = (x4 - x1) / dh;
	mand->delta_yy = (y4 - y1) / dh;

	if ((mand->last_res_x != width) || (mand->last_res_y != height)) {
		mand->pixmap = realloc(mand->pixmap, stride * height * 4);
		mand->last_res_x = width;
		mand->last_res_y = height;
		mand->last_stride = stride;
		mand->last_rend_res = MANDY_REND_RES;
		mand->last_rend_sq = 0;
	}

	if (mand->render) {
		mand->last_rend_res = MANDY_REND_RES;
		mand->last_rend_sq = 0;
		mand->render = 0;
	}
}

void px_blit(mandy *mand, int x, int y, int size, int stride, unsigned int val) {
	unsigned int *ipx = (unsigned int *)mand->pixmap;
	int str = stride / 4;

	int sx = size;
	int sy = size;

	ipx[y * str + x] = val;

	if (x + sx >= mand->last_res_x) {
		sx = mand->last_res_x - x;
	}

	if (y + sy > mand->last_res_y) {
		sy = mand->last_res_y - y;
	}

	for (int yy = y; yy < y + sy; yy++) {
		for (int xx = x; xx < x + sx; xx++) {
			ipx[yy * str + xx] = val;
		}
	}
}

unsigned int rgba(int r, int g, int b, int a) {
	unsigned int ret;

	unsigned char* c_r = (unsigned char *) &ret;
	c_r[0] = (unsigned char) b;
	c_r[1] = (unsigned char) g;
	c_r[2] = (unsigned char) r;
	c_r[3] = (unsigned char) a;

	return ret;
}

PyObject *mandy_get_pixels(mandy *mand, int width, int height, int stride) {
	if (width == 1 || height == 1) {
		width = 32;
		height = 32;
	}

	mandy_gen_info(mand);

	mandy_excl_in(mand);
	mandy_animate(mand);
	mandy_set_display(mand, width, height, stride);
	mandy mnd = *mand;
	mandy_excl_out(mand);

	time_t t = time(NULL);
	if (t != mand->last_t) {
		mand->last_t = t;
		mand->fps = mand->nframes;
		mand->nframes = 0;
	}

	mand->nframes++;

	struct timespec t_start, t_now;
	clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &t_start);
	char *arr = mand->pixmap;
	int bail = 0;

	while(mand->last_rend_res && !bail) {
		int sq_size = 1;
		for (int r = 1; r < mand->last_rend_res; r++)
			sq_size *= 2;

		int w = 1 + width / sq_size;
		int h = 1 + height / sq_size;
		unsigned long mx = h * w;
		int sq_size2 = sq_size * 2;

		int chk_time = 256;
		while(mand->last_rend_sq < mx && !bail) {
			int x = (mand->last_rend_sq % w) * sq_size;
			int y = (mand->last_rend_sq / w) * sq_size;

			int rend = 1;

			if ((x % sq_size2 == 0) && (y % sq_size2 == 0)) {
				rend = 0;
			}

			if ((mand->last_rend_sq == 0) && (mand->last_rend_res == MANDY_REND_RES)) {
				rend = 1;
			}

			if (rend) {
				long double fx = 0;
				long double fy = 0;

				mandy_d2f(&mnd, x, y, &fx, &fy);

				unsigned char v = mandy_v(&mnd, fx, fy);
				unsigned int v_blit = 0;
				unsigned char* v_bl = (unsigned char *) &v_blit;
				int fr = 0;
				int fg = 0;
				int fb = 0;

				if (v > 0) {
					double vv = ((double)v / (double)mnd.miter);
					fr = vv * mnd.fr;
					fg = vv * mnd.fg;
					fb = vv * mnd.fb;
				}

				unsigned int p = y * stride + (x * 4);

				if (sq_size == 1) {
					if (x < width) {
						if (v == 0) {
							arr[p] = 0;
							arr[p + 1] = 0;
							arr[p + 2] = 0;
							arr[p + 3] = 0;
						} else {
							arr[p] = fb;
							arr[p + 1] = fg;
							arr[p + 2] = fr;
							arr[p + 3] = 0;
						}
					}
				} else {
					if (v) {
						v_bl[0] = fb;
						v_bl[1] = fg;
						v_bl[2] = fr;
						v_bl[3] = 0;
					}

					px_blit(mand, x, y, sq_size, stride, v_blit);
				}
			}

			mand->last_rend_sq++;
			chk_time--;
			if (!chk_time) {
				clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &t_now);
				int millis = (t_now.tv_nsec - t_start.tv_nsec) / 1000000;

				if (millis > 23)
					bail = 1;

				chk_time = 256;
			}
		}

		if (!bail) {
			mand->last_rend_res--;
			mand->last_rend_sq = 0;
		}
	}

	unsigned int arrl = stride * height * 4;
	char *arr2 = arr;
	if (mand->active) {
		arr2 = malloc(arrl);
		memcpy(arr2, arr, arrl);

		unsigned int col = rgba(mnd.fr, mnd.fg, mnd.fb, 0);
		render_track(arr2, mand->trk, col, width, height, stride);
	}

	PyObject* ret = PyByteArray_FromStringAndSize(arr2, stride * height * 4);

	if (mand->active)
		free (arr2);

	return ret;
}

void mandy_vect_clear(mandy *mand) {
	mand->nvect =mand->navect = 0;
	free(mand->vect);
	mand->vect = NULL;
}

void mandy_vect_append(mandy *mand, double val) {
	if (mand->nvect == mand->navect) { // need to double
		if (mand->navect == 0)
			mand->navect = 1;

		mand->navect *= 2;
		mand->vect = realloc(mand->vect, sizeof(double) * mand->navect);
	}

	mand->vect[mand->nvect++] = val;
}

unsigned long mandy_render(mandy *mand, int width, int height) {
	mandy_excl_in(mand);
	// update disp-pos
	for (unsigned int t = 0; t < mand->ntracies; t++) {
		tracy *trc = mand->tracies[t];

		mandy_f2d(mand, &trc->disp_x, &trc->disp_y, trc->x, trc->y);
		trc->disp_r = mand->rot - trc->r;
	}

	mandy_f2d(mand, &mand->init_trc->disp_x, &mand->init_trc->disp_y, mand->init_trc->x, mand->init_trc->y);
	mand->init_trc->disp_r = mand->rot - mand->init_trc->rd;

	if (mand->ntracies) {
		tracy *trc = mand->tracies[0];
		for (int t = 0; t < trc->tail_length; t++) {
			mandy_f2d(mand, &trc->tail[t].dx, &trc->tail[t].dy, trc->tail[t].x, trc->tail[t].y);
			trc->tail[t].dr = mand->rot - trc->tail[t].r;
			trc->tail[t].dr += HALFPI;
		}
	}

//	mandy mnd = *mand;
	mandy_excl_out(mand);
	/*
		mandy_excl_vect_in(mand);

		if (mnd.ntracies) {
			tracy *trc = mnd.tracies[0];

			VECT_CLEAR(mand);

			VECT_SET_TYPE(mand, 0);
			VECT_SET_COL(mand, 1);

			float xx = 0;
			float yy = 0;

			mandy_f2d(&mnd, &xx, &yy, trc->x, trc->y);
			VECT_START(mand, xx, yy);

			double rr = trc->rd;
			double rd = rr + M_PI;
			long double x2 = trc->x + trc->unit * cos(rr);
			long double y2 = trc->y + trc->unit * sin(rr);
			long double x1 = trc->x + trc->unit * cos(rd);
			long double y1 = trc->y + trc->unit * sin(rd);

			mandy_f2d(&mnd, &xx, &yy, x2, y2);
			VECT_POINT(mand, xx, yy);
			VECT_END(mand);
		}

		mandy_excl_vect_out(mand);
		*/
	return mand->nvect;
}

unsigned long mandy_get_points(mandy *mand, double *ret_arr, unsigned long l) {
	mandy_excl_vect_in(mand);
	unsigned long v = 0;

	for (; v < mand->nvect && v < l; v++) {
		ret_arr[v] = mand->vect[v];
	}

	mandy_excl_vect_out(mand);
	return v;
}

double mandy_get_zoom(mandy *mand) {
	return mand->zoom;
}

void mandy_set_zoom(mandy *mand, double zoom) {
	mandy_excl_in(mand);
	mand->dzoom = fmin(zoom, 20);

	mand->render = 1;
	mandy_excl_out(mand);
}

double mandy_get_rot(mandy *mand) {
	return mand->rot;
}

void mandy_set_rot(mandy *mand, double rot) {
	mand->drot = fmod(rot, M_PI * 2);
	mand->rot = fmod(mand->rot, M_PI * 2);

	if (mand->rot - mand->drot > M_PI)
		mand->rot -= M_PI * 2;

	if (mand->drot - mand->rot > M_PI)
		mand->rot += M_PI * 2;

	mand->render = 1;
}

double mandy_get_bail(mandy *mand) {
	return mand->bail;
}

void mandy_set_bail(mandy *mand, double bail) {
	if (bail < 1.0)
		bail = 1.0;

	if (bail > mand->miter - 2)
		bail = mand->miter - 2;

	mand->bail = bail;
}

int mandy_get_max_iter(mandy *mand) {
	return MANDY_MAX_ITER;
}

int mandy_get_miter(mandy *mand) {
	return mand->miter;
}

void mandy_set_miter(mandy *mand, int miter) {
	if (miter < 2)
		miter = 2;

	if (miter > MANDY_MAX_ITER)
		miter = MANDY_MAX_ITER;

	if (mand->follow > -1) {
		//mand->tracies[mand->follow]->zoom = 1;
		mand->tracies[mand->follow]->tail_length = 0;
	}

	mand->px = mand->py = -23;

	mand->last_rend_res = MANDY_REND_RES;
	mand->last_rend_sq = 0;
	mand->miter = miter;
	mand->init_trc->unit = 0.1 / pow(MAGIC_MITER2UNIT_RATIO, mand->miter);
	mandy_trc_home(mand, mand->init_trc);
}

char *mandy_get_info(mandy *mand) {
	static char inf[256];

	mandy_excl_in(mand);
	if (mand->info) {
		strcpy(inf, mand->info);
	} else {
		inf[0] = 0;
	}
	mandy_excl_out(mand);
	return inf;
}

void mandy_set_info(mandy *mand, char *info) {
	mandy_excl_in(mand);
	free(mand->info);
	mand->info = NULL;

	if (info == NULL) {
		mandy_excl_out(mand);
		return;
	}

	int l = strlen(info);
	mand->info = malloc(l + 1);
	strcpy(mand->info, info);
	mandy_excl_out(mand);
}

void mandy_set_rgb(mandy *mand, int r, int g, int b) {
	int rend = 0;
	if ((mand->fr != r) ||
	        (mand->fg != g) ||
	        (mand->fb != b))
		rend = 1;

	mand->fr = r;
	mand->fg = g;
	mand->fb = b;
	if (rend)
		mand->render = 1;
}

void mandy_set_xy(mandy *mand, double x, double y) {
	mand->dx = x;
	mand->dy = y;
}

void mandy_set_active(mandy *mand, int active) {
	mand->active = active;
	if (!active) {
		track *trk = (track *)mand->trk;
		trk->resync = 1;
		mand->follow = -1;
	} else {
		if (!mand->ntracies) {
			mandy_add_tracy(mand, mand->init_trc->x, mand->init_trc->y, mand->init_trc->r);
		}
	}
}

int mandy_get_active(mandy *mand) {
	return mand->active;
}

void mandy_set_pause(mandy *mand, int p) {
	mand->pause = p;
	mand->step = 0;
	if (mand->pause) {
		if (mand->ntracies)
			mand->tracies[0]->tail_length = 0;
	}
}

int mandy_get_pause(mandy *mand) {
	return mand->pause;
}

void mandy_step(mandy *mand) {
	mand->step = 1;
	mand->pause = 1;
}

void mandy_reinit_from_scan(mandy *mand) {
	mand->init_trc->x = mand->scan_trc->x;
	mand->init_trc->y = mand->scan_trc->y;
	mand->init_trc->r = mand->scan_trc->r;
	mand->init_trc->unit = mand->scan_trc->unit;

	mandy_trc_home(mand, mand->init_trc);

	if (!mand->ntracies)
		return;

	mand->tracies[0]->ix = mand->init_trc->x;
	mand->tracies[0]->iy = mand->init_trc->y;
	mand->tracies[0]->ir = mand->init_trc->r;

	mandy_reset(mand);

	mandy_f2d(mand, &mand->tracies[0]->disp_x, &mand->tracies[0]->disp_y, mand->tracies[0]->x, mand->tracies[0]->y);
	mand->tracies[0]->disp_r = mand->rot - mand->tracies[0]->rd;
}

// cursor xy
void mandy_set_cxy(mandy *mand, float x, float y) {
	long double fx, fy;
	mandy_d2f(mand, x, y, &fx, &fy);

	int rx;
	int ry;
	int outside;

	if (mandy_pix_scan(&mand->pix_mask, mand->pixmap, x, y, mand->last_res_x, mand->last_res_y, mand->last_stride, &rx, &ry, &outside)) {
		long double dx, dy;
		mandy_d2f(mand, rx, ry, &dx, &dy);
		mand->scan_trc->unit = 0.1 / pow(MAGIC_MITER2UNIT_RATIO, mand->miter);
		mand->scan_trc->x = dx;
		mand->scan_trc->y = dy;

		mand->scan_trc->rd = atan2((ry - y), (rx - x));

		if (!outside) {
			mand->scan_trc->rd += M_PI;
		}

		mand->scan_trc->r = mand->scan_trc->rd;

		mandy_trc_home(mand, mand->scan_trc);
		mandy_f2d(mand, &mand->scan_trc->disp_x, &mand->scan_trc->disp_y, mand->scan_trc->x, mand->scan_trc->y);

		mand->scan_trc->disp_r = mand->rot - mand->scan_trc->rd;

		mand->px = mand->scan_trc->x;
		mand->py = mand->scan_trc->y;
	} else {
		mand->px = -23;
		mand->py = -23;
	}
}

int mandy_get_ntracies(mandy *mand) {
	return mand->ntracies;
}

tracy *mandy_get_tracy(mandy *mand, int trc_id) {
	return mand->tracies[trc_id];
}

tracy *mandy_get_scan_tracy(mandy *mand) {
	if ((int)mand->px != -23) {
		return mand->scan_trc;
	} else {
		return NULL;
	}
}

tracy *mandy_get_init_tracy(mandy *mand) {
	return mand->init_trc;
}

void mandy_del_tracy(mandy *mand, int trc_id) {

	printf("trc del %d\n", mand->ntracies);
}

void mandy_trc_home(mandy *mand, tracy *trc) {
	long double unit = trc->unit;
	double rr = trc->rd;
	double rd = rr + M_PI;
	trc->homed = 0;
	int bail = 0;

	do {
		long double x2 = trc->x + unit * cos(rr);
		long double y2 = trc->y + unit * sin(rr);
		long double x1 = trc->x + unit * cos(rd);
		long double y1 = trc->y + unit * sin(rd);

		long double ix = 0;
		long double iy = 0;

		long double isr = mandy_isect(mand, \
		                              x1, y1,\
		                              x2, y2,\
		                              mand->unit0, &ix, &iy, 0);
		//mand->unit0, &ix, &iy, 0);

		if ((int)isr != -23) {
			trc->homed = 1;
			trc->x = ix;
			trc->y = iy;
			trc->lhx = ix;
			trc->lhy = iy;
			trc->rd = isr + HALFPI;
		} else {
			x2 = trc->x + unit * cos(rr + HALFPI);
			y2 = trc->y + unit * sin(rr + HALFPI);
			x1 = trc->x + unit * cos(rd + HALFPI);
			y1 = trc->y + unit * sin(rd + HALFPI);

			long double isr = mandy_isect(mand,\
			                              x1, y1,\
			                              x2, y2,\
			                              mand->unit0,\
			                              &ix, &iy, 0);

			if ((int)isr != -23 && (unit > trc->unit)) {
				trc->homed = 1;
				trc->x = ix;
				trc->y = iy;
				trc->lhx = ix;
				trc->lhy = iy;
				trc->rd = isr + HALFPI;
			} else {
				unit *= 1.1;
			}
		}

		if (unit > 2 && !trc->homed) {
			bail = 1;
		}

	} while (!trc->homed && (!bail));

	if (bail) {
		trc->bailed = 1;
	}
}

int mandy_trc_is_valid(mandy *mnd, long double unit, long double x, long double y, long double r) {
	int p0, p1, p2, p3;
	long double xx, yy;

	xx = x + unit * cos(r - QPI);
	yy = y + unit * sin(r - QPI);
	p0 = mandy_v(mnd, xx, yy);
	xx = x + unit * cos(r + QPI);
	yy = y + unit * sin(r + QPI);
	p1 = mandy_v(mnd, xx, yy);
	xx = x + unit * cos(r + QPI + HALFPI);
	yy = y + unit * sin(r + QPI + HALFPI);
	p2 = mandy_v(mnd, xx, yy);
	xx = x + unit * cos(r + QPI + M_PI);
	yy = y + unit * sin(r + QPI + M_PI);
	p3 = mandy_v(mnd, xx, yy);

	if ((p2 > 0) && (p3 > 0) && (p0 == 0) && (p1 == 0))
		return 1;

	return 0;
}

void mandy_trc_move(mandy *mnd, tracy *trc, long double l) {
	tracy_add_tail(trc, trc->x, trc->y, trc->speed > 0?trc->rd:trc->rd + M_PI);

	mandy_trc_home(mnd, trc);

	long double togo = l * trc->unit * trc->speed;
	long double gone = 0;

	long double unit = trc->unit;
	long double togo1 = unit;
	if (togo < 0)
		togo1 = -togo1;

	int valid = 0;
	int bail = 48;

	while(fabsf(gone) < fabsf(togo) && bail) {
		long double nx = trc->x + togo1 * cos(trc->rd + HALFPI);
		long double ny = trc->y + togo1 * sin(trc->rd + HALFPI);
		long double nr = 0;

		valid = mandy_trc_is_valid(mnd, unit, nx, ny, trc->rd);

		long double gone1 = 0.0;

		if (valid && bail) {
			// quick home
			long double x1 = nx + unit * cos(trc->rd);
			long double y1 = ny + unit * sin(trc->rd);
			long double x2 = nx + unit * cos(trc->rd + M_PI);
			long double y2 = ny + unit * sin(trc->rd + M_PI);
			nr = mandy_isect(mnd, x1, y1, x2, y2, mnd->unit0, &nx, &ny, 0);

			gone1 = fabsl(sqrtl(pow(nx - trc->x, 2) + pow(ny - trc->y, 2)));
			if (gone + gone1 < fabs(togo) * 1.1 || fabs(togo1) < mnd->unit0) {
				gone += gone1;
				trc->x = nx;
				trc->y = ny;
				trc->rd = nr + HALFPI;
				unit *= 2.0;
				togo1 *= 2.0;
			} else {
				togo1 /= 2.0;
				unit /= 2.0;
				bail--;
			}
		} else {
			togo1 /= 2.0;
			unit /= 2.0;
			bail--;
			if (unit < mnd->unit0) {
				bail = 0;
			}
		}
	}

	if (!bail) {
		trc->bailed = 1;
		if (!valid) {
			// we're cornered
			// take a step back
			double r_d = M_PI / 2;
			if (trc->speed > 0) {
				r_d *= -1;
			}

			trc->x += unit * cos(trc->rd + HALFPI + r_d * .8);
			trc->y += unit * sin(trc->rd + HALFPI + r_d * .8);
			trc->rd += r_d;
		}
	}
}

void mandy_set_follow(mandy *mand, int trc_id) {
	mand->follow = trc_id;

	if ((trc_id < (int)mand->ntracies) && (trc_id > -1)) {
		mand->rot = mand->tracies[mand->follow]->r;
		mand->drot = mand->tracies[mand->follow]->rd;
	}

	mand->render = 1;
}

int mandy_get_follow(mandy *mand) {
	return mand->follow;
}

void mandy_set_julia(mandy *mand, int v) {
	mand->julia = v;
	mand->render = 1;
}

int mandy_get_julia(mandy *mand) {
	return mand->julia;
}

void mandy_set_jxy(mandy *mand, double jx, double jy) {
	mandy_excl_in(mand);
	mand->jx = jx;
	mand->jy = jy;
	mand->jcx = jx;
	mand->jcy = jy;

	mandy_update_julia(mand);

	mand->render = 1;
	mandy_excl_out(mand);
}

double mandy_get_max_speed() {
	return TRACY_MAX_SPEED;
}

void mandy_set_jsx(mandy *mand, double jsx) {
	mand->jsx = jsx;
	mandy_update_julia(mand);
}

void mandy_set_jsy(mandy *mand, double jsy) {
	mand->jsy = jsy;
	mandy_update_julia(mand);
}

void mandy_set_jvx(mandy *mand, double jvx) {
	mand->jvx = jvx;
	mandy_update_julia(mand);
}

void mandy_set_jvy(mandy *mand, double jvy) {
	mand->jvy = jvy;
	mandy_update_julia(mand);
}

double mandy_get_jsx(mandy *mand) {
	return mand->jsx;
}

double mandy_get_jsy(mandy *mand) {
	return mand->jsy;
}

double mandy_get_jvx(mandy *mand) {
	return mand->jvx;
}

double mandy_get_jvy(mandy *mand) {
	return mand->jvy;
}
