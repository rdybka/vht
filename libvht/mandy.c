/* mandy.c - Valhalla Tracker (libvht)
 *
 * Copyright (C) 2020 Remigiusz Dybka - remigiusz.dybka@gmail.com
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
	mand->px = 0.0;
	mand->py = 0.0;
	mand->active = 0;
	mand->pause = 0;
	mand->vect = NULL;
	mand->nvect = 0;
	mand->navect = 0;

	mand->tracies = NULL;
	mand->ntracies = 0;
	mand->follow = -1;
	mand->julia = 0;

	mand->unit0 = 1.0 / pow(2.0, 32.0);

	mand->pixmap = NULL;
	mand->last_res_x = 0;
	mand->last_res_y = 0;
	mand->last_rend_res = MANDY_REND_RES;
	mand->last_rend_sq = 0;
	mand->render = 0;
	mand->nframes_full = 0;
	mand->nframes_adapt = 0;
	mandy_set_display(mand, 32, 32, 32);

	mandy_reset(mand);
	return mand;
}

void mandy_free(mandy *mand) {
	track *trk = (track *)mand->trk;
	trk->mand = NULL;
	free(mand->pixmap);
	free(mand->vect);
	free(mand->tracies);
	pthread_mutex_destroy(&mand->excl);
	pthread_mutex_destroy(&mand->excl_vect);
	free(mand);
}

inline double rad2deg(double r) {
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

void mandy_translate(mandy *mand, float x, float y, float w, float h) {
	long double dx = (x / w * mand->zoom);
	long double dy = (y / w * mand->zoom); // not a typo :]

	rotate(0, 0, mand->rot, &dx, &dy);
	mand->dx -= dx;
	mand->dy -= dy;
	mand->render = 1;
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
		}

		return;
	}

	for (int f = 0; f < n; f++) {
		if (y < 0) {
			mand->dzoom /= mlt;
		} else {
			mand->dzoom *= mlt;
		}
	}
	if (mand->dzoom > 666)
		mand->dzoom = 666;
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

mandy *mandy_clone(mandy *mand, void *vtrk) {
	if (!mand)
		return NULL;

	mandy_excl_in(mand);
	mandy *nmand = mandy_new(vtrk);


	mandy_excl_out(mand);
	return nmand;
}

void mandy_gen_info(mandy *mand) {
	char inf[256];
	sprintf(inf, "fps: %d fpfi: %d\niter: %d\nbail: %.7Lf\nzoom: %.7Lf\nx, y, r = [%.7Lf, %.7Lf, %.3f]\njx, jy = [%.7Lf, %.7Lf]\nsx, sy = [%.7Lf, %.7Lf]\nrgb = [%d, %d, %d]", \
	        mand->fps, mand->nframes_full, mand->miter, mand->bail, mand->zoom, mand->x, mand->y, rad2deg(mand->rot), mand->jx, mand->jy, mand->sx, mand->sy, mand->fr, mand->fg, mand->fb);

	mandy_set_info(mand, inf);
}

void mandy_reset(mandy *mand) {
	mandy_excl_in(mand);
	mand->miter = MANDY_DEF_MITER;
	mand->bail = MANDY_DEF_BAIL;
	mand->bailc = mand->bail;
	mand->bailr = 0.0;
	mand->bailv = 0;
	mand->bails = .2;

	mand->x = -.7;
	mand->dx = mand->x;
	mand->y = 0;
	mand->dy = mand->y;

	mand->jx = 0.0;
	mand->jy = 0.0;
	mand->sx = 0.0;
	mand->sy = 0.0;
	mand->sxv = 0;
	mand->syv = 0;
	mand->sxr = 0;
	mand->syr = 2;
	mand->sxs = 0;
	mand->sys = 0;

	mand->zoom = 6.0;
	mand->dzoom = mand->zoom;
	mand->rot = 0.0;
	mand->drot = mand->rot;

	mand->fps = 0;
	mand->last_t = 0;
	mand->nframes = 0;

	mandy_excl_out(mand);
	mandy_gen_info(mand);
}

// this runs in jack thread
void mandy_advance(mandy *mand, double tperiod, jack_nframes_t nframes) {
	if (!mand)
		return;

	mandy_excl_in(mand);

	if (mand->pause) {
		mandy_excl_out(mand);
		mandy_gen_info(mand);
		return;
	}
	//track *trk = (track *)mand->trk;

	double r = (tperiod / 4) * HALFPI; // one rev per 16 rows

	// bail
	mand->bail = mand->bailc + mand->bailv * cos(mand->bailr);
	mand->bailr += r * mand->bails;

	// sx
	mand->sx = mand->jx + mand->sxv * cos(mand->sxr);
	mand->sy = mand->jy + mand->syv * sin(mand->syr);
	mand->sxr += r * mand->sxs;
	mand->syr += r * mand->sys;

	// update tracies
	for (unsigned int t = 0; t < mand->ntracies; t++) {
		tracy *trc = mand->tracies[t];
		tracy_excl_in(trc);

		trc->unit = 0.1 / pow(1.333, mand->miter);
		mandy_trc_home(mand, trc);
		mandy_trc_move(mand, trc, 1.0);
		trc->r += atan2(sin(trc->rd - trc->r), cos(trc->rd - trc->r)) * trc->r_sm;
		tracy_excl_out(trc);

		if (trc->bailed) {
			trc->bailed = 0;
			printf("bailed!!!\n");
		}
	}

	mandy_excl_out(mand);
	mandy_gen_info(mand);
}

// this runs in gui thread
void mandy_animate(mandy *mand) {
	double sm = 5;
	time_t t = time(NULL);
	if (t != mand->last_t) {
		mand->last_t = t;
		mand->fps = mand->nframes;
		mand->nframes = 0;
	}

	mand->nframes++;
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

		mand->dzoom = mand->tracies[mand->follow]->zoom * mand->tracies[mand->follow]->unit * 100;
		mand->drot = mand->tracies[mand->follow]->r - HALFPI;

		mand->x += (mand->dx - mand->x) / sm;
		mand->y += (mand->dy - mand->y) / sm;

		mand->rot += (mand->drot - mand->rot) / 50;
		mand->zoom += (mand->dzoom - mand->zoom) / sm;

		mand->render = 1;
	} else {
		mand->x = dx;
		mand->y = dy;
		mand->rot = drot;
		mand->zoom = dzoom;
	}
}

// the algo for drawing
inline unsigned char mandy_v(mandy *mand, long double x, long double y) {
	long double xx = mand->sx;
	long double yy = mand->sy;
	long double nx = 0.0;
	long double ny = 0.0;
	long double sx = x;
	long double sy = y;
	unsigned char v = 0;

	for (int f = 0; f < mand->miter; f++) {
		nx = xx*xx - yy*yy + sx;
		ny = 2.0*xx*yy + sy;

		v = f;

		if ((nx*nx+ny*ny) > mand->bail) {
			break;
		}

		xx = nx;
		yy = ny;
	}

	v++;

	if (v == mand->miter)
		v = 0;

	// fix julia
	if (!mand->julia)
		return v;

	unsigned char vv = v;

	xx = x;
	yy = y;
	nx = 0.0;
	ny = 0.0;
	sx = x;
	sy = y;

	for (int f = 0; f < mand->miter; f++) {
		nx = xx*xx - yy*yy + sx;
		ny = 2.0*xx*yy + sy;

		v = f;

		if ((nx*nx+ny*ny) > mand->bail) {
			break;
		}

		xx = nx;
		yy = ny;
	}

	v++;

	if (v == mand->miter)
		vv += 128;

	return vv;
}

// the algo for tracing
inline unsigned char vj(int miter, long double bail, long double x, long double y, long double jx, long double jy) {
	long double xx = jx;
	long double yy = jy;
	long double nx = 0.0;
	long double ny = 0.0;
	long double sx = x;
	long double sy = y;
	unsigned char v = 0;

	for (int f = 0; f < miter; f++) {
		nx = xx*xx - yy*yy + sx;
		ny = 2.0*xx*yy + sy;

		v = f;

		if ((nx*nx+ny*ny) > bail) {
			break;
		}

		xx = nx;
		yy = ny;
	}

	v++;

	if (v == miter)
		v = 0;

	return v;
}

// the god function
long double mandy_isect(int miter, long double bail,\
                        long double x1, long double y1,\
                        long double x2, long double y2,\
                        long double jx, long double jy,\
                        long double unit,\
                        long double *ix, long double *iy,\
                        int norot) { // omit rotation

	unsigned char p1 = vj(miter, bail, x1, y1, jx, jy);
	unsigned char p2 = vj(miter, bail, x2, y2, jx, jy);

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
	unsigned char p3 = vj(miter, bail, x3, y3, jx, jy);

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
		return mandy_isect(miter, bail, x1, y1, x2, y2, jx, jy, unit, ix, iy, norot);
	}

	if (norot) {
		return(-22);
	}

	// let's go deeper to find the angle
	unit /= 10;
	mandy_isect(miter, bail, x1, y1, x2, y2, jx, jy, unit, ix, iy, 1);
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

		unsigned char p3 = vj(miter, bail, lx1, ly1, jx, jy);
		if (!p3 && been_out == 1) {
			mandy_isect(miter, bail, lx1, ly1, lx2, ly2, jx, jy, unit, &lix, &liy, 1);
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
		//memset(mand->pixmap, 0, stride * height * 4);
		mand->last_res_x = width;
		mand->last_res_y = height;
		mand->last_rend_res = MANDY_REND_RES;
		mand->last_rend_sq = 0;
		mand->nframes_adapt = 0;
		mand->nframes_full = 0;
	}

	if (mand->render) {
		mand->last_rend_res = MANDY_REND_RES;
		mand->last_rend_sq = 0;
		mand->render = 0;
		mand->nframes_adapt = 0;
	}
}

void px_blit(mandy *mand, int x, int y, int size, int stride, unsigned int val) {
	unsigned int *ipx = (unsigned int *)mand->pixmap;
	int str = stride / 4;

	int sx = size;
	int sy = size;

	ipx[y * str + x] = val;

	if (x + sx > str) {
		sx = str - x;
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

PyObject *mandy_get_pixels(mandy *mand, int width, int height, int stride) {
	mandy_excl_in(mand);
	mandy_animate(mand);
	mandy_set_display(mand, width, height, stride);
	mandy mnd = *mand;
	mandy_excl_out(mand);

	struct timespec t_start, t_now;
	clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &t_start);
	char *arr = mand->pixmap;
	int bail = 0;

	if (mand->last_rend_res)
		mand->nframes_adapt++;

	while(mand->last_rend_res && !bail) {
		int sq_size = 1;
		for (int r = 1; r < mand->last_rend_res; r++)
			sq_size *= 2;

		int w = 1 + (width / sq_size);
		int h = 1 + (height / sq_size);
		unsigned long mx = h * w;
		int sq_size2 = sq_size * 2;

		int chk_time = 256;
		while(mand->last_rend_sq < mx && !bail) {
			int x = (mand->last_rend_sq % w) * sq_size;
			int y = (mand->last_rend_sq / w) * sq_size;

			int rend = 1;

			if ((x % sq_size2 == 0) && (y % sq_size2 == 0))
				rend = 0;

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

				if (millis > 15)
					bail = 1;

				chk_time = 256;
			}
		}

		if (!bail) {
			mand->last_rend_res--;
			mand->last_rend_sq = 0;
		}
	}

	if (!mand->last_rend_res) {
		mand->nframes_full = mand->nframes_adapt;
	}

	PyObject* ret = PyByteArray_FromStringAndSize(arr, stride * height * 4);
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

		tracy_add_tail(trc, trc->x, trc->y, trc->r);

		for (int t = 0; t < trc->tail_length; t++) {
			mandy_f2d(mand, &trc->tail[t].dx, &trc->tail[t].dy, trc->tail[t].x, trc->tail[t].y);
			trc->tail[t].dr = mand->rot - trc->tail[t].r;
			trc->tail[t].dr += HALFPI;
		}

		mandy_f2d(mand, &trc->disp_x, &trc->disp_y, trc->x, trc->y);
		trc->disp_r = mand->rot - trc->r;
	}

	//mandy mnd = *mand;
	mandy_excl_out(mand);

	mandy_excl_vect_in(mand);
	VECT_CLEAR(mand);
	/*
			VECT_SET_TYPE(mand, 0);
			VECT_SET_COL(mand, 1);

			float xx = 0;
			float yy = 0;

			mandy_f2d(&mnd, &xx, &yy, mnd.px, mnd.py);
			VECT_START(mand, xx, yy);

			long double ix = mnd.x;
			long double iy = mnd.y;

			long double isr = mandy_isect(mand->miter, mand->bail,\
			                              mand->px, mand->py,\
			                              mand->x, mand->y,\
			                              mand->sx, mand->sy,\
			                              mand->zoom / (width),\
			                              &ix, &iy, 0);

			mandy_f2d(&mnd, &xx, &yy, ix, iy);
			VECT_POINT(mand, xx, yy);
			VECT_END(mand);


			VECT_SET_COL(mand, 0);

			VECT_START(mand, xx, yy);

			float xxx = 0;
			float yyy = 0;
			long double l = mand->zoom / 20;

			mandy_f2d(&mnd, &xxx, &yyy, ix + l * cos(isr), iy + l * sin(isr));
			VECT_POINT(mand, xxx, yyy);
			VECT_END(mand);

			VECT_START(mand, xx, yy);

			mandy_f2d(&mnd, &xxx, &yyy, ix + l * cos(isr + M_PI), iy + l * sin(isr + M_PI));
			VECT_POINT(mand, xxx, yyy);
			VECT_END(mand);

			VECT_START(mand, xx, yy);

			mandy_f2d(&mnd, &xxx, &yyy, ix + l / 2 * cos(isr + HALFPI), iy + l / 2 * sin(isr + HALFPI));
			VECT_POINT(mand, xxx, yyy);
			*/
	VECT_END(mand);

	mandy_excl_vect_out(mand);

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
	mand->dzoom = zoom;
	mand->render = 1;
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

int mandy_get_miter(mandy *mand) {
	return mand->miter;
}

void mandy_set_miter(mandy *mand, int miter) {
	if (miter < 2)
		miter = 2;

	if (miter > MANDY_MAX_ITER)
		miter = MANDY_MAX_ITER;

	if (mand->follow > -1) {
		mand->tracies[mand->follow]->zoom = 1;
	}

	mand->last_rend_res = MANDY_REND_RES;
	mand->last_rend_sq = 0;
	mand->nframes_adapt = 0;
	mand->miter = miter;
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
	mand->fr = r;
	mand->fg = g;
	mand->fb = b;
}

void mandy_set_xy(mandy *mand, double x, double y) {
	mand->dx = x;
	mand->dy = y;
}

void mandy_set_active(mandy *mand, int active) {
	mand->active = active;
}
int mandy_get_active(mandy *mand) {
	return mand->active;
}

void mandy_set_pause(mandy *mand, int p) {
	mand->pause = p;
}

int mandy_get_pause(mandy *mand) {
	return mand->pause;
}

// cursor xy
void mandy_set_cxy(mandy *mand, float x, float y) {
	long double fx, fy;
	mandy_d2f(mand, x, y, &fx, &fy);

	if (mand->julia) {
		mand->jx = fx;
		mand->jy = fy;
		mand->render = 1;
	} else {
		mand->px = fx;
		mand->py = fy;
	}
}

int mandy_get_ntracies(mandy *mand) {
	return mand->ntracies;
}

tracy *mandy_get_tracy(mandy *mand, int trc_id) {
	return mand->tracies[trc_id];
}

tracy *mandy_add_tracy(mandy *mand, double ix1, double iy1, double ix2, double iy2) {
	mandy_excl_in(mand);
	tracy *trc = tracy_new(ix1, iy1, ix2, iy2);

	trc->unit = mand->zoom / 100.0;

	trc->homed = 0;
	mand->tracies = realloc(mand->tracies, sizeof (mandy *) * mand->ntracies + 1);
	mand->tracies[mand->ntracies++] = trc;

	long double ix = 0;
	long double iy = 0;

	long double isr = mandy_isect(mand->miter, mand->bail,\
	                              ix1, iy1,\
	                              ix2, iy2,\
	                              mand->sx, mand->sy,\
	                              trc->unit,\
	                              &ix, &iy, 0);

	if ((int)isr != -23) {
		trc->homed = 1;
		trc->x = ix;
		trc->y = iy;
		trc->rd = isr + HALFPI;
	} else {
		mandy_trc_home(mand, trc);
	}

	mandy_excl_out(mand);
	return trc;
}

void mandy_del_tracy(mandy *mand, int trc_id) {
	mandy_excl_in(mand);

	printf("trc del %d\n", mand->ntracies);
	mandy_excl_out(mand);
}

void mandy_trc_home(mandy *mand, tracy *trc) {
	long double unit = trc->unit;
	double rr = trc->rd - M_PI;
	double rd = trc->rd;
	trc->homed = 0;
	int tries = 0;

	do {
		long double x2 = trc->x + unit * cos(rr);
		long double y2 = trc->y + unit * sin(rr);
		long double x1 = trc->x + (unit / 2.0) * cos(rd);
		long double y1 = trc->y + (unit / 2.0) * sin(rd);

		long double ix = 0;
		long double iy = 0;

		long double isr = mandy_isect(mand->miter, mand->bail,\
		                              x1, y1,\
		                              x2, y2,\
		                              mand->sx, mand->sy,\
		                              mand->unit0,\
		                              &ix, &iy, 0);

		//printf("%Lf\n", isr);

		if ((int)isr != -23) {
			trc->homed = 1;
			trc->lhx = trc->x;
			trc->lhy = trc->y;
			trc->x = ix;
			trc->y = iy;
			trc->rd = isr + HALFPI;
		} else {
			unit *= 2;
			trc->tail_length = 0;

			//printf("unit: %.7Lf\n", unit);
		}


		if (unit > 2 && !trc->homed) {
			unit = trc->unit;
			rr += HALFPI;
			rd += HALFPI;
			tries++;
		}

	} while (!trc->homed && (tries < 2));
}

void mandy_trc_move(mandy *mnd, tracy *trc, long double l) {
	if (!trc->homed)
		return;

	long double togo = l * trc->unit * trc->speed;

	trc->x = trc->x + togo * cos(trc->rd + HALFPI);
	trc->y = trc->y + togo * sin(trc->rd + HALFPI);

	mandy_trc_home(mnd, trc);
}

void mandy_set_follow(mandy *mand, int trc_id) {
	if (trc_id < (int)mand->ntracies)
		mand->follow = trc_id;

	mand->render = 1;
	printf("follow %d\n", mand->follow);
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
	mand->render = 1;
	mandy_excl_out(mand);
}

//~ void mandy_trc_move_old(mandy *mnd, tracy *trc, long double l) {
//~ if (!trc->homed)
//~ return;

//~ long double u0 = mnd->unit0;
//~ long double unit = trc->unit;
//~ long double nx = trc->x;
//~ long double ny = trc->y;
//~ long double togo = l * trc->unit * trc->speed;
//~ long double gone = 0.0;
//~ int bail = TRACE_BAIL;

//~ if (togo < unit) {
//~ unit = togo;
//~ }

//~ trc->mtu = unit;

//~ int valid = 0;
//~ while(!valid) {
//~ long double x2 = trc->x + (unit * 10.0) * cos(trc->rd);
//~ long double y2 = trc->y + (unit * 10.0) * sin(trc->rd);
//~ if (0 == vj(mnd->miter, mnd->bail, x2, y2, mnd->sx, mnd->sy)) {
//~ valid = 1;
//~ } else {
//~ unit /= 2.0;
//~ }
//~ }

//~ while(gone < togo && bail) {
//~ long double oldx = trc->x;
//~ long double oldy = trc->y;
//~ double oldr = trc->rd;

//~ // move
//~ nx = trc->x + unit * cos(trc->rd + HALFPI);
//~ ny = trc->y + unit * sin(trc->rd + HALFPI);

//~ trc->x = nx;
//~ trc->y = ny;

//~ mandy_trc_home(mnd, trc);

//~ long double dgone = sqrtl(powl(fabsl(trc->x - oldx), 2.0) + powl(fabsl(trc->y - oldy), 2.0));

//~ int valid = 1;

//~ if (!trc->homed) {
//~ trc->bailed = 1;
//~ valid = 0;
//~ } else if (dgone > unit * 1.05) {
//~ valid = 0;
//~ } else if ((gone + dgone) - togo > (unit * 1.01)) {
//~ valid = 0;
//~ }

//~ if (unit < u0) {
//~ valid = 1;
//~ unit = u0;
//~ }

//~ bail--;

//~ if (bail == 1 && trc->homed) {
//~ valid = 1;
//~ }

//~ if (valid) {
//~ gone += dgone;
//~ if (unit > trc->mtu)
//~ trc->mtu = unit;

//~ unit *= 2.0;

//~ if (unit > trc->unit * 100)
//~ unit = trc->unit * 100;
//~ } else {
//~ unit /= 2.0;
//~ trc->x = oldx;
//~ trc->y = oldy;
//~ trc->rd = oldr;
//~ }


//~ }

//~ if (!bail) {
//~ trc->bailed = 1;
//~ }
//~ }
