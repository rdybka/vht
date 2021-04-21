/* sequence.c - Valhalla Tracker (libvht)
 *
 * Copyright (C) 2020 Remigiusz Dybka - remigiusz.dybka@gmail.com
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
#include <math.h>
#include "module.h"
#include "sequence.h"
#include "track.h"

void seq_mod_excl_in(sequence *seq) {
	//printf("mod_excl in");
	if (seq->mod_excl)
		pthread_mutex_lock(seq->mod_excl);
	//printf(".\n");
}

void seq_mod_excl_out(sequence *seq) {
	//printf("mod_excl out");
	if (seq->mod_excl)
		pthread_mutex_unlock(seq->mod_excl);
	//printf(".\n");
}

sequence *sequence_new(int length) {
	sequence *seq = malloc(sizeof(sequence));
	seq->ntrk = 0;
	seq->trk = 0;
	seq->pos = 0;
	seq->length = length;
	seq->midi_focus = 0;
	seq->last_period = 0;
	seq->index = 0;
	seq->parent = -1;
	seq->rpb = 4;

	for (int t = 0; t < 3; t ++) {
		seq->triggers[t].type = seq->triggers[t].channel = seq->triggers[t].note = 0;
	}

	for (int t = 0; t < 3; t++) {
		seq->trg_times[t] = -1;
	}

	seq->trg_times[3] = 0;

	seq->trg_playmode = 0;
	seq->trg_quantise = 1;
	seq->mod_excl = NULL;
	seq->clt = NULL;
	seq->playing = 0;
	seq->lost = 1;
	seq->thumb_dirty = 1;
	seq->thumb_repr = NULL;
	seq->thumb_last_ring = 0;
	seq->thumb_length = 0;
	seq->thumb_panic = 0;
	seq->extras = NULL;
	seq->loop_active = 0;
	seq->loop_start = -1;
	seq->loop_end = -1;
	return seq;
}

void sequence_strip_parent(sequence *seq) {
	seq->parent = -1;
}

void sequence_trk_reindex(sequence *seq) {
	for (int t = 0; t < seq->ntrk; t++) {
		seq->trk[t]->index = t;
	}

	seq->thumb_dirty = 1;
}

sequence *sequence_clone(sequence *seq) {
	sequence *ns = sequence_new(seq->length);
	ns->mod_excl = seq->mod_excl;
	ns->clt = seq->clt;
	ns->pos = seq->pos;
	ns->rpb = seq->rpb;

	for (int t = 0; t < seq->ntrk; t++) {
		track *trk = track_clone(seq->trk[t]);
		ns->trk = realloc(ns->trk, sizeof(track *) * (ns->ntrk + 1));
		track_wind(trk, seq->pos);
		ns->trk[ns->ntrk++] = trk;
		trk->mod_excl = seq->mod_excl;
		trk->clt = seq->clt;
	}

	sequence_trk_reindex(ns);

	ns->trg_playmode = seq->trg_playmode;
	ns->trg_quantise = seq->trg_quantise;

	for (int t = 0; t < 3; t ++) {
		ns->triggers[t].type = seq->triggers[t].type;
		ns->triggers[t].channel = seq->triggers[t].channel;
		ns->triggers[t].note = seq->triggers[t].note;
	}

	ns->thumb_repr = NULL;
	ns->thumb_dirty = 1;
	ns->parent = seq->parent;
	ns->lost = 1;
	sequence_set_extras(ns, seq->extras);
	return ns;
}

void sequence_add_track(sequence *seq, track *trk) {
	seq_mod_excl_in(seq);

	seq->trk = realloc(seq->trk, sizeof(track *) * (seq->ntrk + 1));
	seq->trk[seq->ntrk++] = trk;
	trk->mod_excl = seq->mod_excl;
	trk->clt = seq->clt;
	sequence_trk_reindex(seq);
	track_wind(trk, seq->pos);
	seq->thumb_dirty = 1;
	seq_mod_excl_out(seq);
	return;
}

track *sequence_clone_track(sequence *seq, track *trk) {
	track *ntrk = track_clone(trk);
	sequence_add_track(seq, ntrk);
	seq->thumb_dirty = 1;
	return ntrk;
}

void sequence_double(sequence *seq) {
	if (seq->length > SEQUENCE_MAX_LENGTH / 2)
		return;

	for (int t = 0; t < seq->ntrk; t++)
		track_double(seq->trk[t]);

	seq->length *= 2;
	seq->thumb_dirty = 1;
}

void sequence_halve(sequence *seq) {
	if (seq->length < 2)
		return;

	for (int t = 0; t < seq->ntrk; t++)
		track_halve(seq->trk[t]);

	seq->length /= 2;
	seq->thumb_dirty = 1;
}

void sequence_free(sequence *seq) {
	for (int t = 0; t < seq->ntrk; t++) {
		track_kill_notes(seq->trk[t]);
		track_free(seq->trk[t]);
	}

	if (seq->trk)
		free(seq->trk);

	if (seq->thumb_repr)
		free(seq->thumb_repr);

	if (seq->extras)
		free(seq->extras);

	free(seq);
}

void sequence_advance(sequence *seq, double period, jack_nframes_t nframes) {
	midi_client *clt = (midi_client *)seq->clt;
	module *mod = (module *)clt->mod_ref;

	if (mod->render_mode == 3)
		return;

	//printf("*** %d %d %d %d -", seq->trg_times[0], seq->trg_times[1], seq->trg_times[2], seq->trg_times[3]);

	if ((seq->trg_quantise == 0) && (seq->trg_times[2] == -2)) {
		seq->trg_times[2] = -1;
		if (seq->playing && seq->trg_times[3] != -2) {
			seq->playing = 0;
			seq->lost = 1;
			for (int t = 0; t < seq->ntrk; t++)
				track_reset(seq->trk[t]);
		} else {
			seq->playing = 1;
			seq->pos = 0;
			if (seq->trg_playmode == TRIGGER_ONESHOT)
				seq->trg_times[3] = -3;

			for (int t = 0; t < seq->ntrk; t++) {
				track_reset(seq->trk[t]);
			}
		}
	}

	//printf("> %d %d %d %d\n", seq->trg_times[0], seq->trg_times[1], seq->trg_times[2], seq->trg_times[3]);

	double p = ceil(seq->pos) - seq->pos;

	if (period - p > 0.00000001) {
		jack_nframes_t frm = nframes;
		frm *= p / period;

		if (frm > 0) {
			period -= p;
			nframes -= frm;
			//printf("re-adv seq %f %d\n", p, frm);
			sequence_advance(seq, p, frm);// :]
		}
	}

	if (seq->pos - floor(seq->pos) < 0.0000001) {
		int r = (int)seq->pos;

		for (int t = 0; t < seq->ntrk; t++) {
			if (seq->trk[t]->mand->active) {
				int qnt = seq->trk[t]->mand->tracies[0]->qnt;
				if (qnt > 0 && r % qnt == 0)
					for (int c = 0; c < seq->trk[t]->ncols; c++) {
						int v = seq->trk[t]->mand_qnt[c];
						if (v > -232323 && v < 0) {
							seq->trk[t]->mand_qnt[c] = abs(v) - 1;
						}
					}
			}
		}

		if (seq->parent == -1 && mod->render_mode != 1 && seq->loop_active) {
			if (r > seq->loop_end || r < seq->loop_start) {
				seq->pos = seq->loop_start;
				r = seq->loop_start;
				for (int t = 0; t < seq->ntrk; t++) {
					track_reset(seq->trk[t]);
					track_wind(seq->trk[t], seq->pos);
				}
			}
		}

		while (r >= seq->length) {
			r-=seq->length;
		}

		//printf("%03d %d %d %d %d\n", r, seq->trg_times[0], seq->trg_times[1], seq->trg_times[2], seq->trg_times[3]);

		// quantised play
		if (seq->trg_times[2] == r) {
			seq->trg_times[2] = -1;
			if (!seq->playing) {
				seq->playing = 1;
				seq->pos = 0;
				if (seq->trg_playmode == TRIGGER_ONESHOT) {
					seq->trg_times[3] = -2;
					if (r == 0)
						seq->trg_times[3]--;
				}

				for (int t = 0; t < seq->ntrk; t++)
					for (int t = 0; t < seq->ntrk; t++)
						track_reset(seq->trk[t]);
			} else {
				seq->playing = 0;
				seq->lost = 1;
				for (int t = 0; t < seq->ntrk; t++)
					track_reset(seq->trk[t]);
			}
		}

		if (seq->trg_playmode == TRIGGER_HOLD && seq->trg_times[3] == -23 && seq->playing) {
			// let it go, let it go
			seq->trg_times[3] = 0;
			seq->playing = 0;
			seq->lost = 1;
			for (int t = 0; t < seq->ntrk; t++) {
				track_kill_notes(seq->trk[t]);
				//track_reset(seq->trk[t]);
			}
		}

		if(r == 0 && seq->trg_playmode == TRIGGER_ONESHOT && seq->playing) {
			if (seq->trg_times[3] < 0) {
				seq->trg_times[3]++;
			}

			if ((seq->trg_times[3] == -1) && (seq->trg_times[2] == -1)) {
				seq->trg_times[3] = 0;
				seq->playing = 0;
				seq->lost = 1;
				for (int t = 0; t < seq->ntrk; t++)
					track_reset(seq->trk[t]);
			}
		}

		// cue trigger
		if (r == 0) {
			if (seq->trg_times[1] > -1) {
				seq->trg_times[1] = -1;

				if (seq->playing) {
					seq->playing = 0;
					for (int t = 0; t < seq->ntrk; t++)
						track_reset(seq->trk[t]);
				} else {
					seq->playing = 1;
					for (int t = 0; t < seq->ntrk; t++)
						track_reset(seq->trk[t]);
				}
			}
		}
	}

	int resync = 0;
	// mute trigger
	if (seq->trg_times[0] > -1) {
		seq->trg_times[0] = -1;

		if(seq->playing) {
			seq->playing = 0;
			for (int t = 0; t < seq->ntrk; t++) {
				track_kill_notes(seq->trk[t]);
			}
		} else {
			seq->playing = 1;
			resync = 1;
		}
	}

	if (resync) {
		for (int t = 0; t < seq->ntrk; t++) {
			seq->trk[t]->resync = 0;
			seq->trk[t]->pos = 0;
			track_wind(seq->trk[t], seq->pos);
			track_advance(seq->trk[t], period, nframes);
		}
	}

	seq->last_period = period;
	if (seq->playing) {
		// resync tracks
		for (int t = 0; t < seq->ntrk; t++) {
			if (seq->trk[t]->resync) {
				seq->trk[t]->resync = 0;
				seq->trk[t]->pos = 0;
				track_wind(seq->trk[t], seq->pos);
				track_advance(seq->trk[t], period, nframes);
			}
		}

		for (int t = 0; t < seq->ntrk; t++) {

			track_advance(seq->trk[t], period, nframes);
		}
	}

	seq->pos += period;

	if (seq->pos >= seq->length) {
		if (mod->render_mode == 1 && seq->playing) {
			mod->render_mode = 3;
			mod->end_time = mod->clt->jack_last_frame;
		}
	}

	if (seq->pos > seq->length) {
		seq->pos -= seq->length;
	}
}

void sequence_del_track(sequence *seq, int t) {
	if (t == -1)
		t = seq->ntrk - 1;

	if ((t >= seq->ntrk) || (t < 0))
		return;

	seq_mod_excl_in(seq);

	track_free(seq->trk[t]);

	for (int i = t; i < seq->ntrk - 1; i++) {
		seq->trk[i] = seq->trk[i + 1];
	}

	seq->ntrk--;

	if (seq->ntrk == 0) {
		free(seq->trk);
		seq->trk = 0;
	} else {
		seq->trk = realloc(seq->trk, sizeof(track *) * seq->ntrk);
	}

	sequence_trk_reindex(seq);
	seq_mod_excl_out(seq);
}

void sequence_swap_track(sequence *seq, int t1, int t2) {
	if ((t1 < 0) || (t1 >= seq->ntrk))
		return;

	if ((t2 < 0) || (t2 >= seq->ntrk))
		return;

	if (t1 == t2)
		return;

	seq_mod_excl_in(seq);

	track *t3 = seq->trk[t1];
	seq->trk[t1] = seq->trk[t2];
	seq->trk[t2] = t3;
	sequence_trk_reindex(seq);
	seq_mod_excl_out(seq);
}

void sequence_set_midi_focus(sequence *seq, int foc) {
	seq->midi_focus = foc;
}

void sequence_set_length(sequence *seq, int length) {
	seq_mod_excl_in(seq);
	for (int t = 0; t < seq->ntrk; t++) {
		if((seq->trk[t]->nrows == seq->trk[t]->nsrows) && (seq->trk[t]->nrows == seq->length)) {
			track_resize(seq->trk[t], length);
			seq->trk[t]->nsrows = length;
		}
	}

	seq->length = length;
	seq->lost = 1;
	seq->thumb_dirty = 1;
	seq_mod_excl_out(seq);
}

int sequence_get_playing(sequence *seq) {
	return seq->playing;
}

int sequence_get_ntrk(sequence *seq) {
	seq_mod_excl_in(seq);
	int ret = seq->ntrk;
	seq_mod_excl_out(seq);
	return ret;
}

double sequence_get_relative_length(sequence *seq) {
	double l = seq->length;
	double rpb = seq->rpb;

	return (4.0 / rpb) * l;
}

int sequence_get_cue(sequence *seq) {
	if (seq->trg_times[1] == -1) {
		return 0;
	} else {
		return 1;
	}
}

void sequence_set_playing(sequence *seq, int p) {
	if (!p) {
		seq->playing = 0;
	} else {
		seq->playing = 1;
	}

	seq->thumb_dirty = 1;
}

void sequence_handle_record(module *mod, sequence *seq, midi_event evt) {
	if (!seq->playing)
		return;

	if (mod->recording == 1)
		if (seq->midi_focus >= 0 && seq->midi_focus < seq->ntrk) {
			track_handle_record(seq->trk[seq->midi_focus], evt);
			evt.channel = seq->trk[seq->midi_focus]->channel;
			midi_buffer_add(mod->clt, seq->trk[seq->midi_focus]->port, evt);
		}

	if (mod->recording == 2) {
		midi_buffer_add(mod->clt, mod->clt->default_midi_port, evt);
		int found = 0;
		for (int tr = seq->ntrk - 1; tr > -1 && !found; tr--) {
			if ((seq->trk[tr]->channel == evt.channel) && (seq->trk[tr]->port == mod->clt->default_midi_port)) {
				track_handle_record(seq->trk[tr], evt);
				found = 1;
			}
		}

		if (!found) {
			track *trk;
			trk = track_new(mod->clt->default_midi_port, evt.channel, seq->length, seq->length, mod->ctrlpr);

			// sequence_add_track(seq, trk); can't call it from here because of bad design
			seq->trk = realloc(seq->trk, sizeof(track *) * (seq->ntrk + 1));
			seq->trk[seq->ntrk++] = trk;
			trk->mod_excl = seq->mod_excl;
			trk->clt = seq->clt;
			sequence_trk_reindex(seq);

			trk->last_pos = seq->pos - seq->last_period;
			trk->pos = seq->pos;
			trk->last_period = seq->last_period;

			if (trk->last_pos < 0) {
				trk->last_pos += seq->length;
			}

			track_handle_record(trk, evt);
			trk->pos = seq->pos;
		}
	}
}

void sequence_trigger_mute(sequence *seq) {
	//printf("mute %d\n", seq->index);
	midi_client *clt = (midi_client *)seq->clt;
	module *mod = (module *)clt->mod_ref;

	if (!mod->playing) {
		seq->playing = !seq->playing;
	} else {
		seq->trg_times[0] = 0;
	}
}


void sequence_trigger_cue(sequence *seq) {
	//printf("cue %d\n", seq->index);
	if (seq->trg_times[1] == -1) {
		seq->trg_times[1] = 0;
	} else {
		seq->trg_times[1] = -1;
	}
}

void sequence_trigger_play_on(sequence *seq, int blk) {
	midi_client *clt = (midi_client *)seq->clt;
	module *mod = (module *)clt->mod_ref;

	if (blk)
		module_excl_in(mod);

	if (!mod->playing)
		goto done;

	if ((seq->trg_playmode == TRIGGER_HOLD) && (seq->playing)) {
		seq->trg_times[3] = 0;
		goto done;
	}

	if (seq->playing) {
		int np = ceil(seq->pos);

		while(np >= seq->length)
			np-=seq->length;

		seq->trg_times[2] = np;
		goto done;
	}

	if (seq->trg_quantise == 0) {
		seq->trg_times[2] = -2;
	} else {
		int np = ceil(seq->pos);

		while(np++ % seq->trg_quantise);
		np--;

		while(np >= seq->length)
			np-=seq->length;

		seq->trg_times[2] = np;
	}

done:
	if (blk)
		module_excl_out(mod);
}

void sequence_trigger_play_off(sequence *seq, int blk) {
	midi_client *clt = (midi_client *)seq->clt;
	module *mod = (module *)clt->mod_ref;

	if (blk)
		module_excl_in(mod);

	if (!mod->playing)
		goto done;

	if (seq->trg_playmode == TRIGGER_HOLD) {
		if (seq->playing) {
			seq->trg_times[3] = -23;
		}  else {
			seq->playing = 0;
			seq->lost = 1;
			seq->pos = 0;
			seq->trg_times[3] = 0;
			seq->trg_times[2] = -1;
			for (int t = 0; t < seq->ntrk; t++)
				track_reset(seq->trk[t]);
		}
	}

done:
	if (blk)
		module_excl_out(mod);
}

int sequence_get_thumb_dirty(sequence *seq) {
	if (seq->thumb_dirty)
		return 1;

	if (seq->thumb_panic)
		return 1;

	for (int t = 0; t < seq->ntrk; t++) {
		if (seq->trk[t]->dirty) {
			seq->thumb_dirty = 1;
			return seq->thumb_dirty;
		}
	}

	seq->thumb_dirty = 1;
	int *oldie = seq->thumb_repr;
	seq->thumb_repr = NULL;
	sequence_gen_thumb(seq);

	if (oldie[0] == seq->thumb_repr[0])
		if (oldie[1] == seq->thumb_repr[1]) {
			int eq = memcmp(oldie, seq->thumb_repr, seq->thumb_length * sizeof(int));
			if (eq == 0) {
				free(oldie);
				return 0;
			}
		}

	free(oldie);
	return 1;
};

int sequence_get_thumb_length(sequence *seq) {
	return seq->thumb_length;
};

int sequence_gen_thumb(sequence *seq) {
	if (seq->thumb_panic) {
		seq->thumb_panic--;
		seq->thumb_dirty = 1;
	}

	if (seq->thumb_dirty) {
		int ncols = 0;
		int tlen = seq->length;

		for (int t = 0; t < seq->ntrk; t++) {
			ncols += seq->trk[t]->ncols;
			if (tlen < seq->trk[t]->nsrows) // funky business
				tlen = seq->trk[t]->nsrows;
		}

		seq->thumb_length = 2 + ncols * tlen;
		seq->thumb_repr = realloc(seq->thumb_repr, seq->thumb_length * sizeof(int));
		memset(seq->thumb_repr, 0, seq->thumb_length * sizeof(int));
		seq->thumb_repr[0] = tlen;
		seq->thumb_repr[1] = ncols;

		int col = 0;
		for (int t = 0; t < seq->ntrk; t++) {
			for (int r = 0; r < seq->trk[t]->nrows; r++) {
				int rr = (int)(((double)seq->trk[t]->nsrows / (double)seq->trk[t]->nrows) * (double)r);
				for (int c = 0; c < seq->trk[t]->ncols; c++) {

					int v = 0;

					if (seq->trk[t]->rows[c][r].type == note_on) {
						v = 1;

						if (seq->trk[t]->ring[c] == seq->trk[t]->rows[c][r].note) {
							if (seq->trk[t]->pos >= r) {
								v = 2;

								for (int yy = seq->trk[t]->pos; yy > r; yy--) {
									if (seq->trk[t]->rows[c][yy].type == note_on)
										v = 1;
								}
							} else {
								v = 2;
								for (int yy = 0; yy < seq->trk[t]->pos; yy++)
									if (seq->trk[t]->rows[c][yy].type > 0)
										v = 1;

								for (int yy = seq->trk[t]->nrows; yy >= r && v == 2; yy--) {
									if ((seq->trk[t]->rows[c][yy].type == note_on) &&
									        (seq->trk[t]->ring[c] == seq->trk[t]->rows[c][yy].note)) {
										if (r != yy)
											v = 1;
									}
								}
							}
						}
					}

					int addr = 2 + (ncols * rr) + col + c;
					if (seq->thumb_panic) {
						if ((v > 0) && (addr < seq->thumb_length))
							seq->thumb_repr[addr] = 3;
					} else {
						if ((v > 0) && (addr < seq->thumb_length))
							seq->thumb_repr[addr] = v;
					}
				}
			}


			col += seq->trk[t]->ncols;
			seq->trk[t]->dirty = 0;
		}

		if (!seq->thumb_panic)
			seq->thumb_dirty = 0;
	}

	return seq->thumb_length;
};

int sequence_get_thumb(sequence *seq, int *ret, int l) {
	if (l != seq->thumb_length)
		return 0;

	memcpy(ret, seq->thumb_repr, l * sizeof(int));
	return l;
};


char *sequence_get_extras(sequence *seq) {
	//printf("xtra: %d %d -> %s\n", seq->parent, seq->index, seq->extras);
	return seq->extras;
}

void sequence_set_extras(sequence *seq, char *extr) {
	//printf("xtra: %p %d %d %s <- %s\n", (void *)seq, seq->parent, seq->index, seq->extras, extr);
	if (extr == NULL) {
		free(seq->extras);
		seq->extras = NULL;
		return;
	}

	free(seq->extras);
	int l = strlen(extr);
	seq->extras = malloc(l + 1);
	strcpy(seq->extras, extr);
}

void sequence_rotate(sequence *seq, int n, int trknum) {
	seq_mod_excl_in(seq);

	for (int t = 0; t < seq->ntrk; t++) {
		track *trk = seq->trk[t];

		if (!trk->playing && trknum == -1)
			continue;

		if (trknum > -1 && t != trknum)
			continue;

		int nn = n;
		while(nn) {
			if (nn > 0) {
				for (int r = trk->nrows - 2; r > -1; r--) {
					track_swap_rows(trk, r, r > 0?r - 1:trk->nrows -1);
				}
			}

			if (nn < 0) {
				for (int r = 1; r < trk->nrows; r++) {
					track_swap_rows(trk, r, r < trk->nrows -1?r + 1:0);
				}
			}

			if (nn > 0)
				nn--;
			if (nn < 0)
				nn++;
		}

		for (int c = 0; c < trk->nctrl; c++)
			envelope_regenerate(trk->env[c], trk->crows[c]);
	}

	seq_mod_excl_out(seq);
}

int sequence_get_loop_active(sequence *seq) {
	if (seq->parent > -1)
		return 0;

	return seq->loop_active;
}

void sequence_set_loop_active(sequence *seq, int v) {
	//int prev = seq->loop_active;
	seq->loop_active = v;

	if (seq->parent > -1) {
		midi_client *clt = (midi_client *)seq->clt;
		module *mod = (module *)clt->mod_ref;
		timeline *tl = mod->tline;
		timestrip *strp = &mod->tline->strips[seq->index];
		double mlt = sequence_get_relative_length(seq) / seq->length;

		if (v) {
			int tls = strp->start;
			tls += round((seq->loop_start * mlt));


			tl->loop_start = tls;

			tls = strp->start;
			tls += round((seq->loop_end + 1) * mlt);

			tl->loop_end = tls;
			tl->loop_active = 1;
			timeline_update_loops_in_strips(tl);
		}

		if (!v) {
			tl->loop_start = strp->start;
			int tls = strp->start;
			tls += round((seq->length) * mlt);
			tl->loop_end = tls;
			tl->loop_active = 0;
			timeline_update_loops_in_strips(tl);
			return;
		}
	}
}

int sequence_get_loop_start(sequence *seq) {
	return seq->loop_start;
}

void sequence_set_loop_start(sequence *seq, int s) {
	if (s < 0)
		s = 0;

	seq->loop_start = s;


	if (seq->parent > -1 && seq->loop_active) {
		midi_client *clt = (midi_client *)seq->clt;
		module *mod = (module *)clt->mod_ref;
		timestrip *strp = &mod->tline->strips[seq->index];

		int tls = strp->start;
		double mlt = sequence_get_relative_length(seq) / seq->length;
		tls += round(s * mlt);

		if (tls < strp->start)
			tls = strp->start;

		mod->tline->loop_start = tls;
	}
}

int sequence_get_loop_end(sequence *seq) {
	return seq->loop_end;
}

void sequence_set_loop_end(sequence *seq, int e) {
	if (e >= seq->length)
		e = seq->length - 1;

	seq->loop_end = e;

	if (seq->parent > -1 && seq->loop_active) {
		midi_client *clt = (midi_client *)seq->clt;
		module *mod = (module *)clt->mod_ref;
		timestrip *strp = &mod->tline->strips[seq->index];

		int tls = strp->start;
		double mlt = sequence_get_relative_length(seq) / seq->length;
		tls += round((e + 1) * mlt);

		mod->tline->loop_end = tls;
	}
}
