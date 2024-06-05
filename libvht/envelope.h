/* envelope.h - vahatraker (libvht)
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

#ifndef __ENVELOPE_H__
#define __ENVELOPE_H__
#include <pthread.h>
#include "ctrlrow.h"

#define ENV_MAX_NNODES	256

typedef struct env_node_t {
	float x;
	float y;
	float z;
	int linked;
} env_node;

typedef struct envelope_t {
	int nnodes;
	env_node *nodes;
	int nrows;
	int res;
	pthread_mutex_t excl;
	float *bzspace;
} envelope;

envelope *envelope_new(int nrows, int ctrlpr);
void envelope_free(envelope *env);
void envelope_del_node(envelope *env, int n);
void envelope_add_node(envelope *env, float x, float y, float z, int linked);
void envelope_set_node(envelope *env, int n, float x, float y, float z, int linked);
void envelope_resize(envelope *env, int nrows, int res);
void envelope_refresh(envelope *env);
void envelope_regenerate(envelope *env, ctrlrow *rows);

float env_get_v(envelope *env, int res, float y);

#endif //__ENVELOPE_H__
