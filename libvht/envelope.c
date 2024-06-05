/* envelope.c - vahatraker (libvht)
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

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "envelope.h"


envelope *envelope_new(int nrows, int res) {
	envelope *env = malloc(sizeof(envelope));

	env->nnodes = 0;
	env->nodes = 0;

	env->nrows = nrows;
	env->res = res;
	pthread_mutex_init(&env->excl, NULL);

	env->bzspace = malloc(sizeof(int) * nrows * res);

	envelope_refresh(env);
	return env;
}

void envelope_free(envelope *env) {
	if(env->nodes)
		free(env->nodes);

	free(env->bzspace);

	pthread_mutex_destroy(&env->excl);
}

void envelope_resize(envelope *env, int nrows, int res) {
	pthread_mutex_lock(&env->excl);

	free(env->bzspace);
	env->bzspace = malloc(sizeof(int) * nrows * res);

	env->nrows = nrows;
	env->res = res;

	envelope_refresh(env);
	pthread_mutex_unlock(&env->excl);
}

float env_get_v(envelope *env, int res, float y) {
	if (!env->nnodes)
		return -1;

	return env->bzspace[(int)y * env->res + (int)((y - floorf(y)) * res)];
}

int env_node_compare(const void *a, const void *b) {
	return (int)((float)((env_node *)a)->y - (float)((env_node *)b)->y);
}

void envelope_sort_nodes(envelope *env) {
	qsort(env->nodes, env->nnodes, sizeof(env_node), env_node_compare);
}

int y2bz(envelope *env, float y) {
	return (int)y * env->res + (int)((y - floorf(y)) * env->res);
}

// with regards to my C mentor - Konrad Wicyński
void envelope_draw_cluster(envelope *env, int nf, int nl) {
	float lx = 0;					// past
	float ly = 0;
	float lz = 0;

	for (int n = nf; n <= nl; n++) {
		float x, y, z;				// present
		float nx, ny;	 			// future

		x = env->nodes[n].x;
		y = env->nodes[n].y;
		z = env->nodes[n].z;

		if (n == nl) { // last node
			nx = x + (x - lx);
			ny = y + (y - ly);
			z = 0;
		} else {
			nx = env->nodes[n + 1].x;
			ny = env->nodes[n + 1].y;
		}

		if (n == nf) { // first node
			lz = 1;
			lx = x - (nx - x);
			ly = y - (ny - y);
		} else {
			lx = env->nodes[n - 1].x;
			ly = env->nodes[n - 1].y;
		}

		if (n == nf + 1) { // second node
			lz = 0;
		}

		int y0 = y2bz(env, ly);
		int y1 = y2bz(env, y);
		float dx = (x - lx) / (y - ly);
		float lny = fabs(y2bz(env, y) - y2bz(env, ly));
		int yend = y2bz(env, env->nodes[nl].y);
		int ystart = y2bz(env, env->nodes[nf].y);

		// straight line from previous node
		float xx = lx + (lz * (x - lx));
		for (int yy = y0 + (lz * lny); yy <  y1; yy++) {
			float l = (yy - y0) / lny;

			if ((l >= lz) && (l < 1.0 - z) && (yy < y1) && (yy < env->nrows * env->res) && (yy >= ystart))
				env->bzspace[yy] = xx;

			xx+=dx / env->res;
		}

		// bezier'ish part
		if (z + lz > 1) {
			z = 1 - lz;
		}

		if (z < 0)
			z = 0;

		lz = z;

		if (z > 0.0) {
			int bzaddr0 = y2bz(env, ly + ((y - ly) * (1 - z)));
			int bzaddr1 = y2bz(env, y + ((ny - y) * z));
			float bzinc = 1.0 / (bzaddr1 - bzaddr0);
			float bzt = 0.0;
			int lbzy = bzaddr0 - 1;

			float bzx0 = x - (x - lx) * z;
			float bzx1 = x + (nx - x) * z;
			float bzy0 = y - (y - ly) * z;
			float bzy1 = y + (ny - y) * z;

			float bzdx0 = (x - bzx0);
			float bzdx1 = bzx1 - x;
			float bzdy0 = (y - bzy0);
			float bzdy1 = bzy1 - y;

			for (int yy = bzaddr0; yy <= bzaddr1; yy++) {
				float p0x = bzx0 + bzdx0 * bzt;
				float p1x = x + bzdx1 * bzt;
				float p0y = bzy0 + bzdy0 * bzt;
				float p1y = y + bzdy1 * bzt;

				float px = p0x + (p1x - p0x) * bzt;
				float py = p0y + (p1y - p0y) * bzt;

				int yyy = (int)(py * env->res);

				while(yyy <= lbzy) {
					bzt+=bzinc;

					p0x = bzx0 + bzdx0 * bzt;
					p1x = x + bzdx1 * bzt;
					p0y = bzy0 + bzdy0 * bzt;
					p1y = y + bzdy1 * bzt;

					px = p0x + (p1x - p0x) * bzt;
					py = p0y + (p1y - p0y) * bzt;
					yyy = (int)(py * env->res);
				}

				while((yyy > lbzy + 1) && (bzinc > .0001)) {
					bzinc *= .5;
					bzt -= bzinc;
					p0x = bzx0 + bzdx0 * bzt;
					p1x = x + bzdx1 * bzt;
					p0y = bzy0 + bzdy0 * bzt;
					p1y = y + bzdy1 * bzt;

					px = p0x + (p1x - p0x) * bzt;
					py = p0y + (p1y - p0y) * bzt;
					yyy = (int)(py * env->res);
				}

				if ((yyy < yend) && (yyy >= ystart)) {
					env->bzspace[yyy] = px;
					lbzy = yyy;
				}

				bzt+=bzinc;
			}
		}
	}
}

void envelope_refresh(envelope *env) {
	envelope_sort_nodes(env);

	for (int y = 0; y < env->res * env->nrows; y++)
		env->bzspace[y] = -1;

	// single nodes
	for (int n = 0; n < env->nnodes; n++) {
		if (!env->nodes[n].linked) {
			if (n <= env->nnodes - 1) {
				if ((n == env->nnodes -1) || (!env->nodes[n + 1].linked)) {
					int yy = y2bz(env, env->nodes[n].y);
					env->bzspace[yy] = env->nodes[n].x;
				}
			}
		}
	}

	// find clusters
	int lnode = -1;
	for (int n = env->nnodes - 1; n >= 0; n--) {
		if (env->nodes[n].z > 1)
			env->nodes[n].z = 1;

		if (env->nodes[n].linked) {
			if (lnode == -1)
				lnode = n;
		} else {
			if (lnode > n) {
				envelope_draw_cluster(env, n, lnode);
				int yy = y2bz(env, env->nodes[lnode].y);
				env->bzspace[yy] = env->nodes[lnode].x;
				lnode = -1;
			}
		}
	}
}

void envelope_regenerate(envelope *env, ctrlrow *rows) {
	pthread_mutex_lock(&env->excl);

	if(env->nodes)
		free(env->nodes);

	env->nnodes = 0;
	env->nodes = 0;

	for (int r = 0; r < env->nrows; r++) {
		if (rows[r].velocity > -1) {
			float smth = (((float)rows[r].smooth) / 9.0);

			if (rows[r].anchor == 0) {
				envelope_add_node(env, rows[r].velocity, r, smth, rows[r].linked);
			} else {
				envelope_add_node(env, rows[r].velocity, (float)((r + 1)) - .01, smth, rows[r].linked);
			}
		}
	}
	envelope_refresh(env);
	pthread_mutex_unlock(&env->excl);
}

void envelope_add_node(envelope *env, float x, float y, float z, int linked) {
	if (env->nnodes >= ENV_MAX_NNODES)
		return;

	env->nodes = realloc(env->nodes, sizeof(env_node) * (env->nnodes + 1));
	env->nodes[env->nnodes].x = x;
	env->nodes[env->nnodes].y = y;
	env->nodes[env->nnodes].z = z;
	env->nodes[env->nnodes].linked = linked;

	env->nnodes++;
}

void envelope_del_node(envelope *env, int n) {
	for (int nn = n; nn < env->nnodes - 1; nn++) {
		env->nodes[nn] = env->nodes[nn + 1];
	}

	env->nodes = realloc(env->nodes, sizeof(env_node) * env->nnodes - 1);
	env->nnodes--;
}

void envelope_set_node(envelope *env, int n, float x, float y, float z, int linked) {
	if ((n < 0) || (n >= env->nnodes))
		return;

	env->nodes[n].x = x;
	env->nodes[n].y = y;
	env->nodes[n].z = z;

	if (linked != -1)
		env->nodes[n].linked = linked;
}
