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
#include "envelope.h"
#include "track.h"

envelope *envelope_new() {
	envelope *env = malloc(sizeof(envelope));

	env->nnodes = 0;
	env->nodes = 0;
	pthread_mutex_init(&env->excl, NULL);
	printf("env added\n");
	return env;
}

void envelope_free(envelope *env) {
	if(env->nodes)
		free(env->nodes);
}

void envelope_add_node(envelope *env, float x, float y, int helper, int linked) {
	pthread_mutex_lock(&env->excl);

	printf("add node %f %f %d %d\n", x, y, helper, linked);



	pthread_mutex_unlock(&env->excl);
}

void envelope_del_node(envelope *env, int n) {
	pthread_mutex_lock(&env->excl);

	pthread_mutex_unlock(&env->excl);
}

void envelope_set_node(envelope *env, int n, float x, float y, int helper, int linked) {
	pthread_mutex_lock(&env->excl);

	pthread_mutex_unlock(&env->excl);
}

// from python, we will access envelopes through track
// all controllers will have envs added automatically
void track_envelope_add_node(track *trk, int c, float x, float y, int helper, int linked) {
	envelope_add_node(trk->env[c], x, y, helper, linked);
}

void track_envelope_del_node(track *trk, int c, int n) {
	envelope_del_node(trk->env[c], n);
}

void track_envelope_set_node(track *trk, int c, int n, float x, float y, int helper, int linked) {
	envelope_set_node(trk->env[c], n, x, y, helper, linked);
}

char *track_get_envelope(track *trk, int c) {
	static char ret[1024];

	sprintf(ret, "[");

	strcat(ret, "]");
	return ret;
}
