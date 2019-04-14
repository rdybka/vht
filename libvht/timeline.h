/* timeline.h
 *
 * Copyright (C) 2019 Remigiusz Dybka
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

#ifndef __TIMELINE_H__
#define __TIMELINE_H__

#include <pthread.h>
#include "strip.h"

typedef struct timeline_t {
	double p_pos;  // play position

	int n_strip;
	strip *strips;

	pthread_mutex_t excl;
} timeline;

timeline *timeline_new();
void timeline_set_pos(timeline *tl, double pos);

#endif //#TIMELINE_H__
