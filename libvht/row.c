/* row.c - vahatraker (libvht)
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
#include "row.h"
#include "midi_client.h"
#include "module.h"

void rw_should_save(row *rw) {
	if (rw->clt) {
		midi_client *clt = (midi_client *)rw->clt;
		module *mod = (module *)clt->mod_ref;
		mod->should_save = 1;
	}
}
int row_get_type(row *rw) {
	return rw->type;
}

int row_get_note(row *rw) {
	return rw->note;
}

int row_get_velocity(row *rw) {
	return rw->velocity;
}

int row_get_delay(row *rw) {
	return rw->delay;
}

int row_get_prob(row *rw) {
	return rw->prob;
}

void row_set_type(row *rw, int type) {
	rw->type = type;
}

void row_set_note(row *rw, int note) {
	rw->note = note;
	rw_should_save(rw);
	row_randomise(rw);
}

void row_set_velocity(row *rw, int velocity) {
	rw->velocity = velocity;
	rw_should_save(rw);
	row_randomise(rw);
}

void row_set_delay(row *rw, int delay) {
	rw->delay = delay;
	rw_should_save(rw);
	row_randomise(rw);
}

void row_set_prob(row *rw, int prob) {
	rw->prob = prob;
	rw_should_save(rw);
	row_randomise(rw);
}

int row_get_velocity_range(row *rw) {
	return rw->velocity_range;
}

int row_get_delay_range(row *rw) {
	return rw->delay_range;
}

void row_set_velocity_range(row *rw, int range) {
	rw->velocity_range = range;
	rw_should_save(rw);
	row_randomise(rw);
}

void row_set_delay_range(row *rw, int range) {
	rw->delay_range = range;
	rw_should_save(rw);
	row_randomise(rw);
}

void row_set(row *rw, int type, int note, int velocity, int delay, int prob, int v_r, int d_r) {
	rw->note = note;
	rw->velocity = velocity;
	rw->delay = delay;
	rw->prob = prob;
	rw->velocity_range = v_r;
	rw->delay_range = d_r;
	rw->velocity_next = velocity;
	rw->delay_next = delay;
	rw->type = type;
	rw_should_save(rw);
	row_randomise(rw);
}

void row_randomise(row *rw) {
	if (rw->type == 0)
		return;

	rw->velocity_next = rw->velocity;
	rw->delay_next = rw->delay;

	int rng = rw->velocity_range;
	if (rng > rw->velocity)
		rng = rw->velocity;

	int rnd = random() % (rng + 1);
	int vel = rw->velocity - rnd;
	if (vel < 0)
		vel = 0;

	rw->velocity_next = vel;

	int dfrom = rw->delay - rw->delay_range;
	int dto = rw->delay + rw->delay_range;

	if (dfrom < -49)
		dfrom = -49;

	if (dto > 49)
		dto = 49;

	rng = dto - dfrom;

	if (rng >= 0) {
		rnd = random() % (rng + 1);
		rw->delay_next = dfrom + rnd;
	}
}
