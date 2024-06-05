/* mandy_pix_scan.c - vahatraker (libvht)
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
#include <math.h>
#include <stdio.h>
#include "mandy_pix_scan.h"

void fix_mask(float **pix_msk) {
	float *pix_mask = *pix_msk;
	if (pix_mask)
		return;

	int sz = 1 + PIX_MASK_SIZE * 2;

	*pix_msk = malloc(sizeof(float) * sz * sz);
	pix_mask = *pix_msk;

	for (int x = 0; x < sz; x++)
		for (int y = 0; y < sz; y++)
			pix_mask[x + y * sz] = fabs(sqrtf(((x - PIX_MASK_SIZE) * (x - PIX_MASK_SIZE)) + (
			                                      (y - PIX_MASK_SIZE) *  (y - PIX_MASK_SIZE))));
}

int mandy_pix_scan(float **pix_msk, char *pixmap, int x, int y, int w, int h, int stride, int *ret_x, int *ret_y, int *out) {
	if (!*pix_msk)
		fix_mask(pix_msk);

	unsigned int *ipx = (unsigned int *)pixmap;
	int strd = stride / 4;
	float *pix_mask = *pix_msk;

	int outside = 1;
	if ((x < w) && (y < h) && (x >= 0) && (y >= 0))
		outside = ipx[x + y * strd]?1:0;

	*out = outside;

	int sz = 1 + PIX_MASK_SIZE * 2;
	float max_dist = PIX_MASK_SIZE;

	*ret_x = 0;
	*ret_y = 0;
	int mx = 0;
	int my = 0;

	for (int yy = y - PIX_MASK_SIZE; yy < y + PIX_MASK_SIZE; yy++) {
		for (int xx = x - PIX_MASK_SIZE; xx < x + PIX_MASK_SIZE; xx++) {
			if ((xx < w) && (yy < h) && (xx > 0) && (yy > 0)) {
				if (pix_mask[mx + my * sz] < max_dist) {
					unsigned int v = ipx[xx + yy * strd];

					if (outside) {
						if (v) {
							v = 0;
						} else {
							v = 1;
						}
					}

					if (v) {
						max_dist = pix_mask[mx + my * sz];
						*ret_x = xx;
						*ret_y = yy;
					}
				}
			}

			mx++;
		}

		my++;
		mx = 0;
	}

	if (*ret_x & *ret_y) {
		return 1;
	}

	return 0;
}
