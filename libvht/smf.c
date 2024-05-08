/* smf.c - vahatraker (libvht)
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
#include "smf.h"
#include "module.h"

const unsigned char timecodes [2] = {0xE2, 0xE7};
const int timecode_fps [2] = {30, 25};

smf *smf_new(void *mod_ref) {
	smf *ret = malloc(sizeof(smf));
	ret->mod_ref = mod_ref;
	ret->ntrk = 0;
	ret->bin = 0;
	ret->ticks = 120;
	ret->tc = 0;
	smf_clear(ret);

	return ret;
}

void smf_free(smf *mf) {
	smf_clear(mf);
}

void smf_clear_bin(smf *mf) {
	if (mf->bin) {
		free(mf->bin);
	}

	mf->bin = 0;
	mf->bin_l = 0;
	mf->bin_a = 0;
}

void smf_clear(smf *mf) {
	for (int t = 0; t < mf->ntrk; t++) {
		if (mf->trk_inf[t].evts)
			free(mf->trk_inf[t].evts);

		mf->trk_inf[t].evts = 0;
		mf->trk_inf[t].nevt = 0;
		mf->trk_inf[t].aevt = 0;
	}

	mf->ntrk = 0;
	mf->curr_frame = 0;
	smf_clear_bin(mf);
}

void smf_set_pos(smf *mf, jack_nframes_t pos) {
	mf->curr_frame = pos;
}

void smf_client_flush(smf *mf, int port, midi_event evt) {
	module *mod = (module *)mf->mod_ref;

	midi_buff_excl_in(mod->clt);

	int found = -1;
	for (int t = 0; t < mf->ntrk; t++) {
		if ((mf->trk_inf[t].chn == evt.channel) && (mf->trk_inf[t].prt == port)) {
			found = t;
		}
	}

	if (found == -1) {
		int t = mf->ntrk;
		mf->trk_inf[t].aevt = SMF_MIN_BUFF;
		mf->trk_inf[t].evts = malloc(sizeof(evthist) * mf->trk_inf[t].aevt);
		mf->trk_inf[t].nevt = 0;
		mf->trk_inf[t].chn = evt.channel;
		mf->trk_inf[t].prt = port;

		// copy name
		mf->trk_inf[t].name[0] = 0;
		for (int s = 0; s < mod->nseq; s++) {
			for (int tt = 0; tt < mod->seq[s]->ntrk; tt++) {
				track *trk = mod->seq[s]->trk[tt];

				if ((trk->channel == evt.channel) && (trk->port == port)) {
					char *b;
					char *xtr = track_get_extras(trk);

					if (xtr) {
						b = strstr(xtr, "\"track_name\": \"");
						if (b) {
							b+=15;
							char *bb = strstr(b, "\"");
							int l = bb - b;
							if (l > 0) {
								strncpy(mf->trk_inf[t].name, b, l);
								mf->trk_inf[t].name[l] = 0;
							}
						}
					}
				}
			}
		}

		found = t;
		mf->ntrk++;
	}

	if (found > -1) {
		if (mf->trk_inf[found].nevt == mf->trk_inf[found].aevt) {
			mf->trk_inf[found].aevt *= 2;
			mf->trk_inf[found].evts = realloc(mf->trk_inf[found].evts, sizeof(evthist) * mf->trk_inf[found].aevt);
		}

		mf->trk_inf[found].evts[mf->trk_inf[found].nevt].evt = evt;
		long tm = mf->curr_frame - mod->zero_time;
		if (tm < 0)
			tm = 0;
		mf->trk_inf[found].evts[mf->trk_inf[found].nevt].time = tm;
		mf->trk_inf[found].nevt++;
	}

	midi_buff_excl_out(mod->clt);
}

void smf_push(smf *mf, unsigned char a) {
	if (mf->bin_a == mf->bin_l) {
		if (mf->bin_a == 0) {
			mf->bin_a = SMF_MIN_BUFF;
		} else {
			mf->bin_a *= 2;
		}

		mf->bin = realloc(mf->bin, mf->bin_a);
	}

	mf->bin[mf->bin_l++] = a;
}

void smf_push_str(smf *mf, char *s) {
	int l = 0;
	while(s[l]) {
		smf_push(mf, s[l++]);
	}
}

void smf_push_evt(smf *mf, uint8_t ch, int chn, long time, midi_event evt) {
	if (time < 0)
		time = 0;

	if (ch == 0xc0) {
		ch += chn - 1;
		smf_push_var(mf, time);
		smf_push(mf, ch);
		smf_push(mf, evt.note);
	} else {
		ch += chn - 1;
		smf_push_var(mf, time);
		smf_push(mf, ch);
		smf_push(mf, evt.note);
		smf_push(mf, evt.velocity);
	}
	//printf("%ld:%02x\n", time, ch);
}

int comp_evts(const void *evt1, const void *evt2) {
	const evthist *e1 = evt1;
	const evthist *e2 = evt2;
	if (e1->time < e2->time) return -1;
	if (e2->time < e1->time) return 1;
	return 0;
}

int smf_dump(smf *mf, const char *phname) {
	module *mod = (module *)mf->mod_ref;

	if (!mf->ntrk)
		return -1;

	mod->playing = 0;

	midi_buff_excl_in(mod->clt);
	smf_clear_bin(mf);

	// write header
	smf_push_str(mf, "MThd");
	smf_push_long(mf, 6);
	smf_push_short(mf, 1);
	smf_push_short(mf, mf->ntrk + 1);
	smf_push(mf, timecodes[mf->tc]);
	smf_push(mf, mf->ticks);
	double smptmult = timecode_fps[mf->tc] * mf->ticks;

	// time-track
	ulong loffs;
	smf_push_str(mf, "MTrk");
	loffs = mf->bin_l;
	smf_push_long(mf, 0);
	smf_push_long(mf, 0x00FF2F00);
	ulong curr = mf->bin_l;
	mf->bin_l = loffs;
	smf_push_long(mf, curr - (loffs + 4));
	mf->bin_l = curr;

	for (int t = 0; t < mf->ntrk; t++) {
		// sort evts
		qsort(mf->trk_inf[t].evts, mf->trk_inf[t].nevt, sizeof(evthist), comp_evts);

		// dump track
		smf_push_str(mf, "MTrk");
		loffs = mf->bin_l;
		smf_push_long(mf, 0);
		// name
		if (mf->trk_inf[t].name[0]) {
			smf_push(mf, 0);
			smf_push_short(mf, 0xff03);
			smf_push(mf, strlen(mf->trk_inf[t].name));
			smf_push_str(mf, mf->trk_inf[t].name);
		}

		// channel
		smf_push_short(mf, 0x00ff);
		smf_push_short(mf, 0x2001);
		smf_push(mf, mf->trk_inf[t].chn - 1);

		unsigned long ltime = 0;

		for (uint ev = 0; ev < mf->trk_inf[t].nevt; ev++) {
			jack_nframes_t tm = mf->trk_inf[t].evts[ev].time;
			midi_event evt = mf->trk_inf[t].evts[ev].evt;
			double dtime = (double)(tm + evt.time) / (double)(mod->clt->jack_sample_rate);
			unsigned long smptime = lround(smptmult * dtime);
			unsigned long smptdelta = smptime - ltime;
			ltime = smptime;

			if (evt.type == note_on)
				smf_push_evt(mf, 0x90, mf->trk_inf[t].chn, smptdelta, evt);

			if (evt.type == note_off)
				smf_push_evt(mf, 0x80, mf->trk_inf[t].chn, smptdelta, evt);

			if (evt.type == control_change)
				smf_push_evt(mf, 0xb0, mf->trk_inf[t].chn, smptdelta, evt);

			if (evt.type == pitch_wheel)
				smf_push_evt(mf, 0xe0, mf->trk_inf[t].chn, smptdelta, evt);

			if (evt.type == program_change)
				smf_push_evt(mf, 0xc0, mf->trk_inf[t].chn, smptdelta, evt);
		}

		smf_push_long(mf, 0x00FF2F00); // end of track
		// fix length
		curr = mf->bin_l;
		mf->bin_l = loffs;
		smf_push_long(mf, curr - (loffs + 4));
		mf->bin_l = curr;
	}

	if (phname) {
		FILE *ph = fopen(phname, "wb");
		fwrite(mf->bin, 1, mf->bin_l, ph);
		fclose(ph);
	}

	midi_buff_excl_out(mod->clt);
	return 0;
}
