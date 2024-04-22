/* smf.h - vahatraker (libvht)
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

#ifndef __SMF_H__
#define __SMF_H__

#include "midi_event.h"

#define SMF_MAX_TRK 1023
#define SMF_MIN_BUFF 2

typedef struct evthist_t {
	jack_nframes_t time;
	midi_event evt;
} evthist;

typedef struct track_info_t {
	int chn;
	int prt;
	char name[256];
	ulong nevt;
	ulong aevt;
	evthist *evts;
} track_info;

typedef struct smf_t {
	void *mod_ref;
	jack_nframes_t curr_frame;
	int8_t *bin;
	int bin_l;
	int bin_a;

	int ntrk;
	track_info trk_inf[SMF_MAX_TRK];
	int ticks;
	int tc;
} smf;

smf *smf_new(void *mod_ref);
void smf_free(smf *mf);
void smf_clear(smf *mf);
int smf_dump(smf *mf, const char *phname);
void smf_client_flush(smf *mf, int port, midi_event evt);
void smf_set_pos(smf *mf, jack_nframes_t frm);

void smf_push(smf *mf, unsigned char a);
void smf_push_long(smf *mf, unsigned long a);
void smf_push_short(smf *mf, unsigned short a);
void smf_push_var(smf *mf, unsigned long value);


#endif //__SMF_H__ 
