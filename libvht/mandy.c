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
	mandy_set_display(mand, 32, 32);

	mandy_reset(mand);
	return mand;
}

void mandy_free(mandy *mand) {
	track *trk = (track *)mand->trk;
	trk->mand = NULL;
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
	sprintf(inf, "fps: %d\niter: %d\nbail: %.7Lf\nzoom: %.7Lf\nx, y, r = [%.7Lf, %.7Lf, %.3f]\nsx, sy = [%.7Lf, %.7Lf]\nrgb = [%d, %d, %d]", \
	        mand->fps, mand->miter, mand->bail, mand->zoom, mand->x, mand->y, rad2deg(mand->rot), mand->sx, mand->sy, mand->fr, mand->fg, mand->fb);

	mandy_set_info(mand, inf);
}

void mandy_reset(mandy *mand) {
	mandy_excl_in(mand);
	mand->miter = MANDY_DEF_MITER;
	mand->bail = MANDY_DEF_BAIL;
	mand->bailc = mand->bail;
	mand->bailr = 0.0;
	mand->bailv = 0.0;
	mand->bails = .2;

	mand->x = -.7;
	mand->dx = mand->x;
	mand->y = 0;
	mand->dy = mand->y;

	mand->sx = 0.0;
	mand->sy = 0.0;
	mand->sxv = 0.2;
	mand->syv = 0.2;
	mand->sxr = 0;
	mand->syr = 0;
	mand->sxs = 0.5;
	mand->sys = 0.5;

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

void mandy_advance(mandy *mand, double tperiod, jack_nframes_t nframes) {
	if (!mand)
		return;

	if (mand->pause) {
		mandy_gen_info(mand);
		return;
	}

	mandy_excl_in(mand);
	//track *trk = (track *)mand->trk;

	double r = (tperiod / 4) * M_PI / 2; // one rev per 16 rows

	// bail
	mand->bail = mand->bailc + mand->bailv * cos(mand->bailr);
	mand->bailr += r * mand->bails;

	// sx
	mand->sx = mand->sxv * cos(mand->sxr);
	mand->sy = mand->syv * sin(mand->syr);
	mand->sxr += r * mand->sxs;
	mand->syr += r * mand->sys;

	mandy_excl_out(mand);
	mandy_gen_info(mand);
}

void mandy_animate(mandy *mand) {
	double sm = 5;
	time_t t = time(NULL);
	if (t != mand->last_t) {
		mand->last_t = t;
		mand->fps = mand->nframes;
		mand->nframes = 0;
	}

	mand->nframes++;

	mand->x += (mand->dx - mand->x) / sm;
	mand->y += (mand->dy - mand->y) / sm;

	mand->rot += (mand->drot - mand->rot) / sm;
	mand->zoom += (mand->dzoom - mand->zoom) / sm;
}

void rotate(long double cx, long double cy, long double r, long double *x, long double *y) {
	long double rr = 0;
	long double l = sqrt(pow((*y - cy), 2) + pow((*x - cx), 2));
	r -= M_PI / 2;

	rr = atan2((*x - cx), (*y - cy));
	rr += r;

	*x = cx + l * cos(rr);
	*y = cy + l * sin(rr);
}

// the algo
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

	return v;
}

void mandy_set_display(mandy *mand, int width, int height) {
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

PyObject *mandy_get_pixels(mandy *mand, int width, int height, int stride) {
	mandy_excl_in(mand);
	mandy_animate(mand);
	mandy_set_display(mand, width, height);
	mandy mnd = *mand;
	mandy_excl_out(mand);

	char *arr = malloc(stride * height * 4);
	memset(arr, 0, stride * height * 4);

	for (int y = 0; y < height; y++)
		for (int x = 0; x < width; x++) {

			long double fx = 0;
			long double fy = 0;

			mandy_d2f(&mnd, x, y, &fx, &fy);

			unsigned char v = mandy_v(&mnd, fx, fy);

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

	PyObject* ret = PyByteArray_FromStringAndSize(arr, stride * height * 4);
	free(arr);
	return ret;
}

void mandy_vect_clear(mandy *mand) {
	mand->nvect =mand->navect = 0;
	free(mand->vect);
	mand->vect = NULL;
}

void mandy_vect_append(mandy *mand, double val) {
	printf("+ %f ", val);

}

unsigned long mandy_render(mandy *mand, int width, int height) {
	mandy_excl_in(mand);
	mandy mnd = *mand;
	mandy_excl_out(mand);

	printf("render %d %d\n", width, height);
	mandy_excl_vect_in(mand);
	mandy_vect_clear(mand);
	VECT_SET_TYPE(mand, 0);

	float xx = 0;
	float yy = 0;

	mandy_f2d(&mnd, &xx, &yy, mnd.px, mnd.py);




	mandy_excl_vect_out(mand);

	printf("\n");
	return mand->nvect;
}

unsigned long mandy_get_points(mandy *mand, double *ret_arr, unsigned long l) {
	mandy_excl_vect_in(mand);




	mandy_excl_vect_out(mand);
	return 0;
}

void mandy_translate(mandy *mand, float x, float y, float w, float h) {
	long double dx = (x / w * mand->zoom);
	long double dy = (y / w * mand->zoom); // not a typo :]

	rotate(0, 0, mand->rot, &dx, &dy);
	mand->dx -= dx;
	mand->dy -= dy;
}

void mandy_rotate(mandy *mand, float x, float y, float w, float h) {
	mand->drot += x / w * M_PI;
}

void mandy_zoom(mandy *mand, float x, float y, float w, float h) {
	double mlt = 1.05;
	int n = abs(ceil(y));

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

double mandy_get_zoom(mandy *mand) {
	return mand->zoom;
}

void mandy_set_zoom(mandy *mand, double zoom) {
	mand->dzoom = zoom;
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

void mandy_set_cxy(mandy *mand, float x, float y) {
	long double fx, fy;
	mandy_d2f(mand, x, y, &fx, &fy);
	mand->px = fx;
	mand->py = fy;
}
