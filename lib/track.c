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
 
 #include <stdlib.h>
 
 #include "module.h"
 #include "track.h"
 #include "row.h"
 
track *track_new(track *trk_clone) {
	if (!trk_clone) {
		track *trk = malloc(sizeof(track));
		trk->channel = 0;
		trk->nrows = module.def_nrows;
		trk->nsrows = module.def_nrows;
		trk->trigger_channel = 0;
		trk->trigger_note = 0;
		trk->loop = 0;
		trk->trigger_type = TRIGGER_NORMAL;
		trk->ncols = 1;
		
		trk->rows = malloc(sizeof(row**) * trk->nrows);
		
		for (int t = 0; t < trk->nrows; t++)
		{
			trk->rows[t] = malloc(sizeof( row *) * trk->ncols);
			for (int c = 0; c < trk->ncols; c++) {
				trk->rows[t][c].note = 0;
				trk->rows[t][c].velocity = 0;
				trk->rows[t][c].delay = 0;
			}
		}
		
		return trk;
	}
};

void track_free(track *trk) {
	for (int r = 0; r < trk->nrows; r++) {
		free(trk->rows[r]);
	}

	free(trk->rows);
	free(trk);
};
