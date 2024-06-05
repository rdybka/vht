/* mandy_trk_disp.c - vahatraker (libvht)
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


#include "mandy_trk_disp.h"

char alph[][16] = {"a # "
                   "# #"
                   "###"
                   "# #"
                   "# #",
                   "b## "
                   "# #"
                   "## "
                   "# #"
                   "## ",
                   "c ##"
                   "#  "
                   "#  "
                   "#  "
                   " ##",
                   "d## "
                   "# #"
                   "# #"
                   "# #"
                   "## ",
                   "e ##"
                   "#  "
                   "## "
                   "#  "
                   " ##",
                   "f ##"
                   "#  "
                   "## "
                   "#  "
                   "#  ",
                   "g ##"
                   "#  "
                   "# #"
                   "# #"
                   " # ",
                   "## #"
                   "###"
                   "# #"
                   "###"
                   "# #",
                   "0 # "
                   "# #"
                   "# #"
                   "# #"
                   " # ",
                   "1 # "
                   " # "
                   " # "
                   " # "
                   " # ",
                   "2## "
                   "  #"
                   "## "
                   "#  "
                   "###",
                   "3###"
                   "  #"
                   " ##"
                   "  #"
                   "###",
                   "4# #"
                   "# #"
                   "###"
                   "  #"
                   "  #",
                   "5###"
                   "#  "
                   "## "
                   "  #"
                   "## ",
                   "6###"
                   "#  "
                   "###"
                   "# #"
                   "###",
                   "7###"
                   "  #"
                   "  #"
                   "  #"
                   "  #",
                   "8###"
                   "# #"
                   "###"
                   "# #"
                   "###",
                   "9###"
                   "# #"
                   "###"
                   "  #"
                   "###",
                   "-   "
                   "   "
                   "###"
                   "   "
                   "   ",
                   "=   "
                   "###"
                   "   "
                   "###"
                   "   ",
                   "\0"
                  };

unsigned int col_mix(unsigned int cols, unsigned int cold, float mix) {
	unsigned int ret = cols;
	unsigned char *cs = (unsigned char *) &cols;
	unsigned char *cd = (unsigned char *) &cold;
	unsigned char *cr = (unsigned char *) &ret;

	for (int f = 0; f < 4; f++) {
		cr[f] = cs[f] + (cd[f] - cs[f]) * mix;
	}

	return ret;
}

void render_letter(char ltr, unsigned int col, char *pix, int x, int y, int stride, int h) {
	unsigned int *ipx = (unsigned int *)pix;
	int str = stride / 4;

	char *ltrd = NULL;
	int l = 0;
	while (alph[l][0] != 0 && !ltrd) {
		if (alph[l][0] == ltr)
			ltrd = alph[l] + 1;
		l++;
	}

	if (!ltrd)
		return;

	int hh = h / 2;

	float alpha = (y % hh) / (float)hh;
	if (y > h - 2)
		alpha = 1;

	if (y < hh) {
		alpha = 1 - alpha;
	}

	if (alpha < 0)
		alpha = 0;

	if (alpha > 1)
		alpha = 1;

	for (int yy = y; yy < y + 5; yy++) {
		for (int xx = x; xx < x + 3; xx++) {
			if (ltrd[0] == '#') {
				if ((yy >= 0) && (yy < h))
					ipx[yy * str + xx] = col_mix(col, ipx[yy * str + xx], alpha);
			}

			ltrd++;
		}
	}
}

void note2buff(unsigned int i, char *buff) {
	static char *notes[] = {"c-", "c#", "d-", "d#", "e-", "f-", "f#", "g-", "g#", "a-", "a#", "b-"};

	int oct = i / 12;
	int note = i%12;

	if (oct > 0) {
		sprintf(buff, "%s%x", notes[note], oct - 1);
	} else {
		sprintf(buff, "%s<", notes[note]);
	}
}

void render_track(char *pix, track *trk, unsigned int col, int w, int h, int stride) {
	unsigned int *ipx = (unsigned int *)pix;
	int str = stride / 4;
	int hh = h / 2;
	int rwh = 7;
	int rwoffs = (trk->pos - floorf(trk->pos)) * rwh;
	int rup = hh / rwh;
	int r = trk->pos;
	r -= rup;
	int y = hh - (rup * rwh) - rwoffs;
	int rend_w = trk->ncols * 16 + 14;
	rend_w += 16 * trk->nctrl;
	int x0 = w - rend_w;

	while (y < h) {
		int rw = r;
		while (rw >= trk->nrows)
			rw -= trk->nrows;
		while (rw < 0)
			rw += trk->nrows;

		char buff[16];
		sprintf(buff, "%03d", rw);

		for (int b = 0; b < 3; b++) {
			render_letter(buff[b], 0, pix, 1 + x0 + 2 + b * 4, 1 + y, stride, h);
			render_letter(buff[b], col, pix, x0 + 2 + b * 4, y, stride, h);
		}

		for (int c = 0; c < trk->ncols; c++) {
			char r[10];

			r[0] = '-';
			r[1] = '-';
			r[2] = '-';

			if (trk->rows[c][rw].type == note_off) {
				r[0] = '=';
				r[1] = '=';
				r[2] = '=';
			}

			if (trk->rows[c][rw].type == note_on) {
				note2buff(trk->rows[c][rw].note, r);
			}

			for(int rr = 0; rr < 3; rr++) {
				render_letter(r[rr], 0, pix, 1 + x0 + 16 + rr * 4 + (c * 14), 1 + y, stride, h);
				render_letter(r[rr], col, pix, x0 + 16 + rr * 4 + (c * 14), y, stride, h);
			}
		}

		// add controllers
		for (int c = 0; c < trk->nctrl; c++) {
			for (int yy = 0; yy < rwh; yy++) {
				int crw = rw * trk->ctrlpr + ((float)yy / (float)rwh) * trk->ctrlpr;
				float dt = env_get_v(trk->env[c], trk->ctrlpr, (float)crw / (float)trk->ctrlpr);
				int data = dt;

				if (data == -1) {
					data = trk->ctrl[c][crw];

					if ((data > -1) && (c == 0)) { // pitchwheel
						data /= 128;
					}
				}

				if (data > -1) {
					int xx0 = 1 + x0 + 16 + (trk->ncols * 14) + c * 16;
					int xs = 0;
					int xe = round(14 * data / 127);

					if (c == 0) {
						xs = 7;

						if (xe < xs) {
							int xm = xs;
							xs = xe;
							xe = xm;
						}
					}

					int y0 = (y + yy) - 1;
					if ((y0 < h) && (y0 > -1)) {
						int hh = h / 2;

						float alpha = (y0 % hh) / (float)hh;
						if (y0 > h - 2)
							alpha = 1;

						if (y0 < hh) {
							alpha = 1 - alpha;
						}

						if (alpha < 0)
							alpha = 0;

						if (alpha > 1)
							alpha = 1;

						for (int xx = xs; xx < xe; xx++) {
							int addr = y0 * str + xx0 + xx;
							ipx[addr] = col_mix(col, ipx[addr], alpha);
						}
					}
				}
			}
		}

		if ((rw == 0) && (y > 0) && (y < h))
			for (int xx = 0; xx < 3; xx++) {
				ipx[(y - 1) * str + x0 + xx] |= col;
			}

		y+=rwh;
		r++;
	}

	int yy = h / 2;
	for (int xx = 0; xx < rend_w; xx++) {
		int addr = yy * str + x0 + xx;
		ipx[addr] = col_mix(0xFFFFFF, ipx[addr], .2);
	}
}



