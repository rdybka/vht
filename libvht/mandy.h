/* mandy.h - Valhalla Tracker (libvht)
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

#ifndef __MANDY_H__
#define __MANDY_H__

#include <pthread.h>
#include <time.h>
#include <Python.h>
#include <jack/jack.h>

#define MANDY_DEF_MITER  3
#define MANDY_MAX_ITER  64
#define MANDY_DEF_BAIL   4
#define MANDY_MAX_MULTS 33

typedef struct tracey_t {
	long double x, y, r, sx, sy, b;
	long double lx, ly, lr, lsx, lsy, lb; // previous state
	int i, li;
	long double i2zr;  	// iterations to zoom ratio
	long double unit;  	// "pixel" size
	int forward;	// 0 - left, 1 - right
	int homed;
} tracey;

typedef struct mandy_t {
	int miter;

	// d* - destination
	// *c - centre
	// *r - angle
	// *v - velocity
	// *s - speed

	long double bail;
	long double bailc;
	long double bailr;
	long double bailv;
	long double bails;

	long double x, y;
	long double dx, dy;

	long double sx, sy;		// "julia noise"
	long double sxr, syr;
	long double sxv, syv;
	long double sxs, sys;

	long double zoom;
	long double dzoom;
	long double rot;
	long double drot;

	// fractal rgb
	int fr, fg, fb;

	// screen
	long double x1, y1;  	// top-left corner
	long double delta_xx;	// pix/length in fractal space
	long double delta_xy;
	long double delta_yy;
	long double delta_yx;
	long double x0, y0;	// top-left corner untotated
	long double delta_x;	// unrotated
	long double delta_y;

	double px, py; // pointer

	// vector drawing
	double *vect;
	unsigned int nvect;
	unsigned int navect;
	pthread_mutex_t excl_vect;

	void *trk;
	char *info;
	int active;
	int pause;
	pthread_mutex_t excl;
	int fps;
	time_t last_t;
	int nframes;
} mandy;


// internal
void mandy_excl_in(mandy *mand);
void mandy_excl_out(mandy *mand);
void mandy_excl_vect_in(mandy *mand);
void mandy_excl_vect_out(mandy *mand);
void mandy_advance(mandy *mand, double tperiod, jack_nframes_t nframes);
void mandy_set_display(mandy *mand, int width, int height);
void mandy_set_info(mandy *mand, char *info);

// public
mandy *mandy_new(void *trk);
void mandy_free(mandy *mand);
void mandy_reset(mandy *mand);
mandy *mandy_clone(mandy *mand, void *trk);

char *mandy_get_info(mandy *mand);

double mandy_get_zoom(mandy *mand);
void mandy_set_zoom(mandy *mand, double zoom);

double mandy_get_rot(mandy *mand);
void mandy_set_rot(mandy *mand, double rot);

double mandy_get_bail(mandy *mand);
void mandy_set_bail(mandy *mand, double bail);

int mandy_get_miter(mandy *mand);
void mandy_set_miter(mandy *mand, int miter);

void mandy_set_active(mandy *mand, int active);
int mandy_get_active(mandy *mand);

void mandy_set_pause(mandy *mand, int p);
int mandy_get_pause(mandy *mand);

unsigned long mandy_render(mandy *mand, int width, int height);
unsigned long mandy_get_points(mandy *mand, double *ret_arr, unsigned long l);
void mandy_vect_clear(mandy *mand);
void mandy_vect_append(mandy *mand, double val);

void mandy_set_xy(mandy *mand, double x, double y);
void mandy_set_rgb(mandy *mand, int r, int g, int b);

// rotations
void mandy_set_cxy(mandy *mand, float x, float y);
void mandy_set_nrots(mandy *mand, int n);

// returns an RGB24 ByteArray
PyObject *mandy_get_pixels(mandy *mand, int width, int height, int stride);

// those take mouse vector and display size and try to make the best of it,
// otherwise you can just modify the struct, it's a state machine
void mandy_translate(mandy *mand, float x, float y, float w, float h);
void mandy_rotate(mandy *mand, float x, float y, float w, float h);
void mandy_zoom(mandy *mand, float x, float y, float w, float h);

// drawing macros
#define VECT_SET_TYPE(m, t) {\
    mandy_vect_append(m, 0);\
    mandy_vect_append(m, t);\
    };

#define VECT_START(m, x, y) {\
    mandy_vect_append(m, 1);\
    mandy_vect_append(m, x);\
    mandy_vect_append(m, y);\
    };

#define VECT_POINT(m, x, y) {\
    mandy_vect_append(m, 2);\
    mandy_vect_append(m, x);\
    mandy_vect_append(m, y);\
    }

#define VECT_END(m) {\
    mandy_vect_append(m, 3);\
    }

#endif //__MANDY_H__
