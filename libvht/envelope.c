/* envelope.c - Valhalla Tracker
 *
 * Copyright (C) 2018 Remigiusz Dybka
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
#include "track.h"

envelope *envelope_new(int nrows, int res) {
	envelope *env = malloc(sizeof(envelope));

	env->nnodes = 0;
	env->nodes = 0;

	env->nrows = nrows;
	env->res = res;
	pthread_mutex_init(&env->excl, NULL);

	env->bzspace = malloc(sizeof(int) * nrows * res);

	for (int y = 0; y < nrows * res; y++)
		env->bzspace[y] = -1;

	return env;
}

void envelope_free(envelope *env) {
	if(env->nodes)
		free(env->nodes);

	free(env->bzspace);

	pthread_mutex_destroy(&env->excl);
}

int env_get_v(envelope *env, int res, float y) {
	if (!env->nnodes)
		return -1;

	return env->bzspace[(int)y * env->res + (int)((y - floorf(y)) * res)];

	int v = -1;

	// single node
	float rr = 1.0 / (float)res;
	for (int n = 0; n < env->nnodes; n++) {
		if ((!env->nodes[n].linked) && (y >= env->nodes[n].y) && (y - env->nodes[n].y < (rr))) {
			v = env->nodes[n].x;
			return v;
		}
	}

	// are we between two nodes?
	int n1 = -1;
	int n2 = 666;
	int h = -1;

	for (int n = 0; n < env->nnodes; n++) {
		if ((env->nodes[n].y <= y) && (n > n1))
			n1 = n;

		if ((env->nodes[n].y > y) && (n < n2))
			n2 = n;
	}

	if ((n1 == -1) || (n2 == 666))
		return -1; // clearly not

	// if bottom is linked, does it have a linked node after it?
	if (env->nodes[n2].linked) {
		if (n2 < env->nnodes - 1)
			if (env->nodes[n2+1].linked)
				h = n2++;
	}

	// same for top
	if (h == -1)
		if (env->nodes[n1].linked) {
			if (n1 > 0)
				h = n1--;
		}

	// is bottom node linked or helper?
	if (!(env->nodes[n2].linked))
		return -1;

	printf("n1:%d h:%d n2:%d \n", n1, h, n2);

	// no helper - simple interpolation
	if (h == -1) {
		double delta = (env->nodes[n2].x - env->nodes[n1].x) / (env->nodes[n2].y - env->nodes[n1].y);
		v = env->nodes[n1].x + (delta * (y - env->nodes[n1].y));
		return v;
	}

	// helper - bezier'ish interpolation
	double ll = env->nodes[n2].y - env->nodes[n1].y;
	double l1 = env->nodes[h].y - env->nodes[n1].y;
	double l2 = env->nodes[n2].y - env->nodes[h].y;
	double l = y - env->nodes[n1].y;

	double ld1 = l1 / ll;
	double ld2 = l2 / ll;

	double y1 = ld1 * l;
	double y2 = ld2 * l;

	double wl = ((l1 + y2) - l1) / ll;
	wl *= l;
	wl += y1;

	//wl = l;

	double delta1 = ((env->nodes[h].x - env->nodes[n1].x) / ll);
	double delta2 = ((env->nodes[n2].x - env->nodes[h].x) / ll);
	double p1 = -(delta1 * ll) + env->nodes[n1].x + (delta1 * 2 * wl);
	double p2 = (env->nodes[h].x - (delta2 * ll)) + (delta2 * 2 * wl);
	v = p1 + (((p2 - p1) / ll) * wl);

	printf("%f %f %f %f %f %f / %f\n", l, ld1, ld2, y1, y2, wl, ll);

	return v;
}

int env_node_compare(const void *a, const void *b) {
	return (int)(420 * ((float)((env_node *)a)->y - (float)((env_node *)b)->y));
}

void envelope_sort_nodes(envelope *env) {
	qsort(env->nodes, env->nnodes, sizeof(env_node), env_node_compare);
}

int y2bz(envelope *env, float y) {
	return (int)y * env->res + (int)((y - floorf(y)) * env->res);
}

void envelope_draw_cluster(envelope *env, int nf, int nl) {
	printf("Drawing %d -> %d\n", nf, nl);
	for (int n = nf; n < nl + 1; n++) {
		float lx, ly, lz;	// past
		float x, y, z;		// present
		float nx, ny, nz;	// future

		x = env->nodes[n].x;
		y = env->nodes[n].y;
		z = env->nodes[n].z;

		if (n == nl) { // last node
			nz = 1;
			nx = x + (x - lx);
			ny = y + (y - ly);
		} else {
			nx = env->nodes[n + 1].x;
			ny = env->nodes[n + 1].y;
			nz = env->nodes[n + 1].z;
		}

		if (n == nf) { // first node
			lz = 1;
			lx = x - (nx - x);
			ly = y - (ny - y);
		} else {
			lx = env->nodes[n - 1].x;
			ly = env->nodes[n - 1].y;
			lz = env->nodes[n - 1].z;
		}

		printf("n:%d\n%7f,%7f,%7f\n%7f,%7f,%7f\n%7f,%7f,%7f\n", n, lx, ly, lz, x, y, z, nx, ny, nz);

		// line from top
		float z2d = 1 - (z + lz);
		float xx = lx;

		if (z2d > 0) {
			int y0 = y2bz(env, ly);
			int y1 = y2bz(env, y);
			y0 += (y1 - y0) * z2d;
			xx += (x - lx) * z2d;

			float dx = (x - lx) / (y - ly);
			for (int yy = y0; yy < y1; yy++) {
				env->bzspace[yy] = xx;
				xx+=(dx / env->res);
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
			if (n < env->nnodes - 1) {
				if (!env->nodes[n + 1].linked)
					env->bzspace[y2bz(env, env->nodes[n].y)] = env->nodes[n].x;
			} else { // last node
				env->bzspace[y2bz(env, env->nodes[n].y)] = env->nodes[n].x;
			}
		}
	}
	// find clusters
	int lnode = -1;
	for (int n = env->nnodes - 1; n >= 0; n--) {
		if (env->nodes[n].linked) {
			if (lnode == -1)
				lnode = n;
		} else {
			if (lnode > n) {
				envelope_draw_cluster(env, n, lnode);
				lnode = -1;
			}
		}
	}
}

void envelope_add_node(envelope *env, float x, float y, float z, int linked) {
	if (env->nnodes >= ENV_MAX_NNODES)
		return;

	pthread_mutex_lock(&env->excl);

	env->nodes = realloc(env->nodes, sizeof(env_node) * (env->nnodes + 1));
	env->nodes[env->nnodes].x = x;
	env->nodes[env->nnodes].y = y;
	env->nodes[env->nnodes].z = z;
	env->nodes[env->nnodes].linked = linked;

	env->nnodes++;

	envelope_refresh(env);
	pthread_mutex_unlock(&env->excl);
}

void envelope_del_node(envelope *env, int n) {
	pthread_mutex_lock(&env->excl);

	for (int nn = n; nn < env->nnodes - 1; nn++) {
		env->nodes[nn] = env->nodes[nn + 1];
	}

	env->nodes = realloc(env->nodes, sizeof(env_node) * env->nnodes - 1);
	env->nnodes--;

	envelope_refresh(env);
	pthread_mutex_unlock(&env->excl);
}

void envelope_set_node(envelope *env, int n, float x, float y, float z, int linked) {
	//printf("node_set: %d: %f:%f:%f %d\n", n, x, y, z, linked);

	pthread_mutex_lock(&env->excl);

	env->nodes[n].x = x;
	env->nodes[n].y = y;
	env->nodes[n].z = z;

	if (linked != -1)
		env->nodes[n].linked = linked;

	envelope_refresh(env);
	pthread_mutex_unlock(&env->excl);
}

// from python, we will access envelopes through track
// all controllers will have envs added automatically
void track_envelope_add_node(track *trk, int c, float x, float y, float z, int linked) {
	envelope_add_node(trk->env[c], x, y, z, linked);
}

void track_envelope_del_node(track *trk, int c, int n) {
	envelope_del_node(trk->env[c], n);
}

void track_envelope_set_node(track *trk, int c, int n, float x, float y, float z, int linked) {
	envelope_set_node(trk->env[c], n, x, y, z, linked);
}

char *track_get_envelope(track *trk, int c) {
	static char ret[(ENV_MAX_NNODES * 40) + 2];

	sprintf(ret, "[");

	for (int n = 0; n < trk->env[c]->nnodes; n++) {
		char buff[256];
		sprintf(buff, "{\"x\":%07.2f,\"y\":%07.2f,\"z\":%07.2f,\"l\":%d},", trk->env[c]->nodes[n].x,
		        trk->env[c]->nodes[n].y, trk->env[c]->nodes[n].z, trk->env[c]->nodes[n].linked);

		strcat(ret, buff);
	}

	strcat(ret, "]");
	return ret;
}
