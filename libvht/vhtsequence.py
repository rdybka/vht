# vhtsequence.py - Valhalla Tracker (libvht)
#
# Copyright (C) 2019 Remigiusz Dybka - remigiusz.dybka@gmail.com
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

from collections.abc import Iterable
from libvht.vhttrack import VHTTrack
import libvht


class VHTSequence(Iterable):
    def __init__(self, vht, seq, cb_new_track=[]):
        super(VHTSequence, self).__init__()
        self._vht_handle = vht
        self._seq_handle = seq
        self.cb_new_track = cb_new_track

    def __len__(self):
        return self._vht_handle.sequence_get_ntrk(self._seq_handle)

    def __int__(self):
        return int(self._seq_handle)

    def __iter__(self):
        for itm in range(self.__len__()):
            yield VHTTrack(
                self._vht_handle,
                self._vht_handle.sequence_get_trk(self._seq_handle, itm),
            )

    def __getitem__(self, itm):
        if itm >= self.__len__():
            raise IndexError()

        if itm == -1:
            if not len(self):
                raise IndexError()

            return VHTTrack(
                self._vht_handle,
                self._vht_handle.sequence_get_trk(self._seq_handle, self.__len__() - 1),
            )

        return VHTTrack(
            self._vht_handle, self._vht_handle.sequence_get_trk(self._seq_handle, itm)
        )

    def add_track(self, port=0, channel=1, length=-1, songlength=-1, ctrlpr=-1):
        if length == -1:
            length = self.length

        trk = self._vht_handle.track_new(port, channel, length, songlength, ctrlpr)
        self._vht_handle.sequence_add_track(self._seq_handle, trk)
        for cb in self.cb_new_track:
            cb(self.index, self._vht_handle.track_get_index(trk))
        return self[self.__len__() - 1]

    def clone_track(self, trk, dest=-1):
        if dest == -1:
            dest = self
        ntrk = self._vht_handle.sequence_clone_track(dest._seq_handle, trk._trk_handle)
        # self._vht_handle.track_set_playing(ntrk, 0)
        for cb in self.cb_new_track:
            cb(self.index, self._vht_handle.track_get_index(ntrk))
        return VHTTrack(self._vht_handle, ntrk)

    def double(self):
        self._vht_handle.sequence_double(self._seq_handle)

    def halve(self):
        self._vht_handle.sequence_halve(self._seq_handle)

    def swap_track(self, t1, t2):
        self._vht_handle.sequence_swap_track(self._seq_handle, t1, t2)

    def del_track(self, t=-1):
        if t >= 0:
            self[t].kill_notes()

        self._vht_handle.sequence_del_track(self._seq_handle, t)

    def set_midi_focus(self, foc):
        self._vht_handle.sequence_set_midi_focus(self._seq_handle, foc)

    @property
    def pos(self):
        return self._vht_handle.sequence_get_pos(self._seq_handle)

    @property
    def length(self):
        return self._vht_handle.sequence_get_length(self._seq_handle)

    @length.setter
    def length(self, value):
        self._vht_handle.sequence_set_length(self._seq_handle, value)

    @property
    def max_length(self):
        return self._vht_handle.sequence_get_max_length()

    @property
    def index(self):
        return self._vht_handle.sequence_get_index(self._seq_handle)

    @property
    def trg_playmode(self):
        return self._vht_handle.sequence_get_trg_playmode(self._seq_handle)

    @trg_playmode.setter
    def trg_playmode(self, value):
        self._vht_handle.sequence_set_trg_playmode(self._seq_handle, value)

    @property
    def trg_quantise(self):
        return self._vht_handle.sequence_get_trg_quantise(self._seq_handle)

    @trg_quantise.setter
    def trg_quantise(self, value):
        self._vht_handle.sequence_set_trg_quantise(self._seq_handle, value)

    def get_trig(self, t):
        return eval(self._vht_handle.sequence_get_trig(self._seq_handle, t))

    def set_trig(self, t, tp, ch, nt):
        self._vht_handle.sequence_set_trig(self._seq_handle, t, tp, ch, nt)

    def __str__(self):
        ret = ""
        for itm in self:
            ret = ret + itm.__str__()
            ret = ret + "\n"

        return ret
