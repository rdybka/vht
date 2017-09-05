/* track.c
 *
 * Copyright (C) 2017 Remigiusz Dybka
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
#include <pthread.h>

#include "module.h"
#include "track.h"
#include "row.h"

track *track_new(int port, int channel, int len, int songlen) {
    track *trk = malloc(sizeof(track));
    trk->channel = 0;
    trk->nrows = len;
    trk->nsrows = songlen;
    trk->trigger_channel = 0;
    trk->trigger_note = 0;
    trk->loop = 0;
    trk->trigger_type = TRIGGER_NORMAL;
    trk->ncols = 1;

    pthread_mutex_init(&trk->excl, NULL);

    trk->rows = malloc(sizeof(row*) * trk->ncols);
    for (int c = 0; c < trk->ncols; c++) {
        trk->rows[c] = malloc(sizeof(row) * trk->nrows);
        track_clear_rows(trk, c);
    }

    return trk;
};


void track_set_row(track *trk, int c, int n, row_type type, int note, int velocity, int delay) {
    pthread_mutex_lock(&trk->excl);

    row *r = &trk->rows[c][n];
    r->type = type;
    r->note = note;
    r->velocity = velocity;
    r->delay = delay;

    pthread_mutex_unlock(&trk->excl);
}

int track_get_row(track *trk, int c, int n, row *r) {
    if ((c >= trk->ncols) || (n >= trk->nrows)) {
        fprintf(stderr, "Invalid track address [%d:%d]\n", c, n);
        return -1;
    }

    if (r == NULL) {
        fprintf(stderr, "Destination row==NULL\n");
        return -1;
    }

    pthread_mutex_lock(&trk->excl);
    row *s = &trk->rows[c][n];
    r->type = s->type;
    r->note = s->note;
    r->velocity = s->velocity;
    r->delay = s->delay;

    pthread_mutex_unlock(&trk->excl);

    return 0;
}

void track_free(track *trk) {
    pthread_mutex_destroy(&trk->excl);
    for (int c = 0; c < trk->ncols; c++) {
        free(trk->rows[c]);
    }

    free(trk->rows);
    free(trk);
}

void track_clear_rows(track *trk, int c) {
    pthread_mutex_lock(&trk->excl);

    for (int t = 0; t < trk->nrows; t++) {
        trk->rows[c][t].type = NONE;
        trk->rows[c][t].note = 0;
        trk->rows[c][t].velocity = 0;
        trk->rows[c][t].delay = 0;
    }

    pthread_mutex_unlock(&trk->excl);
}

track *track_clone(track *src) {
    track *dst = track_new(src->port, src->channel, src->nrows, src->nsrows);
    // todo: copy cols and shit
    return dst;
}
