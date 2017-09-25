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
#include <math.h>

#include "module.h"
#include "track.h"
#include "row.h"
#include "midi_event.h"

track *track_new(int port, int channel, int len, int songlen) {
    track *trk = malloc(sizeof(track));
    trk->channel = channel;
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

        trk->ring = malloc(sizeof(int) * trk->ncols);
    };

// insert random data - should probably get deleted one day
    float s = 0;
    for (int n = 0; n < trk->nrows; n+=2) {
        row *r = &trk->rows[0][n];
        r->type = note_on;
        r->note = 64 + (16.0 * (sin(s)));
        r->velocity = 100;

        s += 0.3;
    }

    track_reset(trk);
    return trk;
};

void track_reset(track *trk) {
    trk->fpos = 0.0;
    trk->npos = -1;
    for (int f = 0; f < trk->ncols; f++)
        trk->ring[f] = -1;
}

void track_set_row(track *trk, int c, int n, int type, int note, int velocity, int delay) {
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

    free(trk->ring);
    free(trk->rows);
    free(trk);
}

void track_clear_rows(track *trk, int c) {
    pthread_mutex_lock(&trk->excl);

    for (int t = 0; t < trk->nrows; t++) {
        trk->rows[c][t].type = none;
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

// yooohoooo!!!
void track_trigger(track *trk, int pos, int delay) {
    for (int c = 0; c < trk->ncols; c++) {
        row r;
        track_get_row(trk, c, pos, &r);

        if (r.type == none)
            return;

        midi_event evt;

        if (r.type == note_on) {
            if (trk->ring[c] != -1) {
                evt.time = delay;
                evt.channel = trk->channel;
                evt.type = note_off;
                evt.note = trk->ring[c];
                evt.velocity = 0;
                midi_buffer_add(evt);

                trk->ring[c] = -1;

                char desc[256];
                midi_describe_event(evt, desc, 256);
                printf("%02d:%02d:%03d %02d:%s\n", module.min, module.sec, module.ms, trk->npos, desc);
            }
        }

        evt.time = delay;
        evt.channel = trk->channel;
        evt.type = r.type;
        evt.note = r.note;
        evt.velocity = r.velocity;
        midi_buffer_add(evt);

        if (r.type == note_on) {
            trk->ring[c] = r.note;
        }

        char desc[256];
        midi_describe_event(evt, desc, 256);
        printf("%02d:%02d:%03d %02d:%s\n", module.min, module.sec, module.ms, trk->npos, desc);
    }
}

void track_advance(track *trk, float speriod) {
    // length of period in track time
    float tperiod = (float)trk->nrows / (float)trk->nsrows;
    tperiod *= speriod;

    int n = floorf(trk->fpos);

    // trigger?
    if (trk->npos != n) {
        track_trigger(trk, n, 0);
    }

    trk->npos = n;
    trk->fpos += tperiod;

    if (trk->fpos > trk->nrows)
        trk->fpos -= trk->nrows;
}
