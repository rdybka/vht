/* module.h
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

#include "module.h"

struct module_t module;

int add_sequence(int seq_clone) {
    // fresh module
    if (module.nseq == 0) {
        module.seq = malloc(sizeof(sequence *));
        module.seq[0] = sequence_new();
        module.nseq = 1;
        return 1;
    }
}

void module_new() {
    module_free();
    module.bpm = 123;
    module.def_nrows = 64;
    module.rpb = 4;
    module.seq = NULL;
    module.nseq = 0;
    module.curr_seq = 0;

    add_sequence(-1);
    sequence_add_track(module.seq[0], track_new(0, 1, module.def_nrows, module.def_nrows));
}

void module_free() {
    // fresh start?
    if (module.bpm == 0) {
        return;
    }

    if (module.seq != NULL) {
        for (int s = 0; s < module.nseq; s++)
            sequence_free(module.seq[s]);

        free(module.seq);
        module.seq = NULL;
        module.bpm = 0;
    }
}
