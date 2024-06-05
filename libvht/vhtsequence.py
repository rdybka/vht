# vhtsequence.py - vahatraker (libvht)
#
# Copyright (C) 2024 Remigiusz Dybka - remigiusz.dybka@gmail.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import math

from collections.abc import Iterable
from libvht.vhttrack import VHTTrack
from libvht.vhtextras import VHTExtras
from libvht import libcvht


class VHTSequence(Iterable):
    def __init__(self, seq, mod, cb_new_track=[]):
        super(VHTSequence, self).__init__()
        self._mod = mod
        self._seq_handle = seq
        self.cb_new_track = cb_new_track
        self._extras = None

    def __len__(self):
        return libcvht.sequence_get_ntrk(self._seq_handle)

    def __int__(self):
        return int(self._seq_handle)

    def __iter__(self):
        for itm in range(self.__len__()):
            yield VHTTrack(libcvht.sequence_get_trk(self._seq_handle, itm))

    def __eq__(self, other):
        if type(other) is not VHTSequence:
            return False

        h1 = int(self._seq_handle)
        h2 = int(other._seq_handle)
        if h1 == h2:
            return True

        return False

    def __hash__(self):
        return int(self._seq_handle)

    def __getitem__(self, itm):
        if itm >= self.__len__():
            return None

        if itm < 0:
            if not len(self) >= -itm:
                raise IndexError()

            return VHTTrack(
                libcvht.sequence_get_trk(self._seq_handle, self.__len__() + itm)
            )

        return VHTTrack(libcvht.sequence_get_trk(self._seq_handle, itm))

    def add_track(self, port=0, channel=1, length=-1, songlength=-1, ctrlpr=-1):
        if length == -1:
            length = self.length

        trk = libcvht.track_new(port, channel, length, songlength, ctrlpr)
        libcvht.sequence_add_track(self._seq_handle, trk)
        for cb in self.cb_new_track:
            cb(self.index, libcvht.track_get_index(trk))
        return self[self.__len__() - 1]

    def clone_track(self, trk, dest=None):
        if dest == None:
            dest = self
        ntrk = libcvht.sequence_clone_track(dest._seq_handle, trk._trk_handle)
        # libcvht.track_set_playing(ntrk, 0)
        for cb in self.cb_new_track:
            cb(dest.index, libcvht.track_get_index(ntrk))
        return VHTTrack(ntrk)

    def double(self):
        tstr = None
        ind = self.index
        if type(ind) is tuple:
            tstr = self._mod.timeline.strips[ind[1]]
            if not tstr.can_resize(self.length * 2):
                return

        libcvht.sequence_double(self._seq_handle)

        if tstr:
            if self.relative_length > tstr.length:
                if (
                    self._mod.timeline.loop.start == tstr.start
                    and self._mod.timeline.loop.end - self._mod.timeline.loop.start
                    == tstr.length
                ):
                    self._mod.timeline.loop.end = tstr.start + tstr.seq.relative_length

                tstr.length = self.relative_length

        libcvht.timeline_update(self._mod.timeline._tl_handle)

    def halve(self):
        ind = self.index

        tstr = None
        if type(ind) is tuple:
            tstr = self._mod.timeline.strips[ind[1]]
            if tstr.length != tstr.seq.relative_length:
                tstr = None

        libcvht.sequence_halve(self._seq_handle)

        if tstr:
            if (
                self._mod.timeline.loop.start == tstr.start
                and self._mod.timeline.loop.end - self._mod.timeline.loop.start
                == tstr.length
            ):
                self._mod.timeline.loop.end = tstr.start + tstr.seq.relative_length

            tstr.length = self.relative_length

        libcvht.timeline_update(self._mod.timeline._tl_handle)

    def swap_track(self, t1, t2):
        libcvht.sequence_swap_track(self._seq_handle, t1, t2)

    def del_track(self, t):
        libcvht.sequence_del_track(self._seq_handle, t)

    def set_midi_focus(self, foc):
        libcvht.sequence_set_midi_focus(self._seq_handle, foc)

    def rotate(self, val, trk=-1):
        libcvht.sequence_rotate(self._seq_handle, int(val), int(trk))

    @property
    def loop_active(self):
        return True if libcvht.sequence_get_loop_active(self._seq_handle) else False

    @loop_active.setter
    def loop_active(self, v):
        libcvht.sequence_set_loop_active(self._seq_handle, int(v))

    @property
    def loop_start(self):
        return libcvht.sequence_get_loop_start(self._seq_handle)

    @property
    def loop_end(self):
        return libcvht.sequence_get_loop_end(self._seq_handle)

    @loop_start.setter
    def loop_start(self, v):
        libcvht.sequence_set_loop_start(self._seq_handle, int(v))

    @loop_end.setter
    def loop_end(self, v):
        libcvht.sequence_set_loop_end(self._seq_handle, int(v))

    @property
    def pos(self):
        return libcvht.sequence_get_pos(self._seq_handle)

    @pos.setter
    def pos(self, p):
        libcvht.sequence_set_pos(self._seq_handle, float(p))

    @property
    def rpb(self):
        return libcvht.sequence_get_rpb(self._seq_handle)

    @rpb.setter
    def rpb(self, value):
        if 0 < value <= 32:
            tstr = None
            ind = self.index
            if type(ind) is tuple:
                tstr = self._mod.timeline.strips[ind[1]]
                if not tstr.can_rpb(value):
                    return

            libcvht.sequence_set_rpb(self._seq_handle, value)

            if tstr:
                tstr.length = int(math.ceil(tstr.seq.relative_length))
                libcvht.timeline_update(self._mod.timeline._tl_handle)

    @property
    def cue(self):
        if libcvht.sequence_get_cue(self._seq_handle) > 0:
            return True
        else:
            return False

    @property
    def playing(self):
        return libcvht.sequence_get_playing(self._seq_handle)

    @playing.setter
    def playing(self, value):
        libcvht.sequence_set_playing(self._seq_handle, value)

    def ketchup(self):
        libcvht.sequence_set_lost(self._seq_handle, 1)

    @property
    def length(self):
        return libcvht.sequence_get_length(self._seq_handle)

    @length.setter
    def length(self, value):
        tstr = None
        ind = self.index
        if type(ind) is tuple:
            tstr = self._mod.timeline.strips[ind[1]]
            if not tstr.can_resize(value):
                return

        libcvht.sequence_set_length(self._seq_handle, value)

        if tstr:
            if (
                self._mod.timeline.loop.start == tstr.start
                and self._mod.timeline.loop.end - self._mod.timeline.loop.start
                == tstr.length
            ):
                self._mod.timeline.loop.end = tstr.start + tstr.seq.relative_length

            tstr.length = tstr.seq.relative_length
            libcvht.timeline_update(self._mod.timeline._tl_handle)

    @property
    def relative_length(self):
        return libcvht.sequence_get_relative_length(self._seq_handle)

    @property
    def max_length(self):
        return libcvht.sequence_get_max_length()

    @property
    def parent(self):
        return libcvht.sequence_get_parent(self._seq_handle)

    @parent.setter
    def parent(self, value):
        if value is None:
            libcvht.sequence_set_parent(self._seq_handle, -1)
        else:
            libcvht.sequence_set_parent(self._seq_handle, int(value))

    @property
    def index(self):
        idx = libcvht.sequence_get_index(self._seq_handle)
        par = libcvht.sequence_get_parent(self._seq_handle)
        if par > -1:
            return 0, idx
        else:
            return idx

    @property
    def thumb_dirty(self):
        return libcvht.sequence_get_thumb_dirty(self._seq_handle)

    @property
    def thumb(self):
        tl = libcvht.sequence_gen_thumb(self._seq_handle)
        ret_arr = libcvht.int_array(tl)
        libcvht.sequence_get_thumb(self._seq_handle, ret_arr, tl)
        return ret_arr

    @property
    def trg_playmode(self):
        return libcvht.sequence_get_trg_playmode(self._seq_handle)

    @trg_playmode.setter
    def trg_playmode(self, value):
        libcvht.sequence_set_trg_playmode(self._seq_handle, value)

    @property
    def trg_quantise(self):
        return libcvht.sequence_get_trg_quantise(self._seq_handle)

    @trg_quantise.setter
    def trg_quantise(self, value):
        libcvht.sequence_set_trg_quantise(self._seq_handle, value)

    @property
    def extras(self):
        if not self._extras:
            self._extras = VHTExtras(self._get_extras, self._set_extras)
        return self._extras

    def get_trig_grp(self, g):
        return libcvht.sequence_get_trg_grp(self._seq_handle, g)

    def set_trig_grp(self, g, v):
        return libcvht.sequence_set_trg_grp(self._seq_handle, g, v)

    @trg_playmode.setter
    def trg_playmode(self, value):
        libcvht.sequence_set_trg_playmode(self._seq_handle, value)

    def _set_extras(self, value):
        libcvht.sequence_set_extras(self._seq_handle, value)

    def _get_extras(self):
        return libcvht.sequence_get_extras(self._seq_handle)

    def get_trig(self, t):
        return eval(libcvht.sequence_get_trig(self._seq_handle, t))

    def set_trig(self, t, tp, ch, nt):
        libcvht.sequence_set_trig(self._seq_handle, t, tp, ch, nt)

    def trigger_mute(self):
        libcvht.sequence_trigger_mute(self._seq_handle, -1)

    def trigger_mute_forward(self):
        libcvht.sequence_trigger_mute_forward(self._seq_handle, -1)

    def trigger_mute_back(self):
        libcvht.sequence_trigger_mute_back(self._seq_handle, -1)

    def trigger_cue(self):
        libcvht.sequence_trigger_cue(self._seq_handle, -1)

    def trigger_cue_forward(self):
        libcvht.sequence_trigger_cue_forward(self._seq_handle, -1)

    def trigger_cue_back(self):
        libcvht.sequence_trigger_cue_back(self._seq_handle, -1)

    def trigger_play_on(self):
        libcvht.sequence_trigger_play_on(self._seq_handle, -1)

    def trigger_play_off(self):
        libcvht.sequence_trigger_play_off(self._seq_handle, -1)

    @property
    def next_row(self):
        return libcvht.sequence_get_next_row(self._seq_handle)

    def __str__(self):
        ret = ""
        for itm in self:
            ret = ret + itm.__str__()
            ret = ret + "\n"

        return ret
