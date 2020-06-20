# vhtsequence.py - Valhalla Tracker (libvht)
#
# Copyright (C) 2020 Remigiusz Dybka - remigiusz.dybka@gmail.com
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
from libvht import libcvht


class VHTSequence(Iterable):
    def __init__(self, seq, cb_new_track=[]):
        super(VHTSequence, self).__init__()
        self._seq_handle = seq
        self.cb_new_track = cb_new_track

    def __len__(self):
        return libcvht.sequence_get_ntrk(self._seq_handle)

    def __int__(self):
        return int(self._seq_handle)

    def __iter__(self):
        for itm in range(self.__len__()):
            yield VHTTrack(libcvht.sequence_get_trk(self._seq_handle, itm))

    def __getitem__(self, itm):
        if itm >= self.__len__():
            raise IndexError()

        if itm == -1:
            if not len(self):
                raise IndexError()

            return VHTTrack(
                libcvht.sequence_get_trk(self._seq_handle, self.__len__() - 1)
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

    def clone_track(self, trk, dest=-1):
        if dest == -1:
            dest = self
        ntrk = libcvht.sequence_clone_track(dest._seq_handle, trk._trk_handle)
        # libcvht.track_set_playing(ntrk, 0)
        for cb in self.cb_new_track:
            cb(dest.index, libcvht.track_get_index(ntrk))
        return VHTTrack(ntrk)

    def double(self):
        libcvht.sequence_double(self._seq_handle)

    def halve(self):
        libcvht.sequence_halve(self._seq_handle)

    def swap_track(self, t1, t2):
        libcvht.sequence_swap_track(self._seq_handle, t1, t2)

    def del_track(self, t):
        libcvht.sequence_del_track(self._seq_handle, t)

    def set_midi_focus(self, foc):
        libcvht.sequence_set_midi_focus(self._seq_handle, foc)

    @property
    def pos(self):
        return libcvht.sequence_get_pos(self._seq_handle)

    @property
    def rpb(self):
        return libcvht.sequence_get_rpb(self._seq_handle)

    @rpb.setter
    def rpb(self, value):
        if value:
            libcvht.sequence_set_rpb(self._seq_handle, min(max(1, value), 32))
            # self.timeline.changes[0] = [0, self.bpm, self.rpb, 0]

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
        libcvht.sequence_set_length(self._seq_handle, value)

    @property
    def max_length(self):
        return libcvht.sequence_get_max_length()

    @property
    def index(self):
        return libcvht.sequence_get_index(self._seq_handle)

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

    def get_trig(self, t):
        return eval(libcvht.sequence_get_trig(self._seq_handle, t))

    def set_trig(self, t, tp, ch, nt):
        libcvht.sequence_set_trig(self._seq_handle, t, tp, ch, nt)

    def trigger_mute(self):
        libcvht.sequence_trigger_mute(self._seq_handle)

    def trigger_cue(self):
        libcvht.sequence_trigger_cue(self._seq_handle)

    def trigger_play_on(self):
        libcvht.sequence_trigger_play_on(self._seq_handle)

    def trigger_play_off(self):
        libcvht.sequence_trigger_play_off(self._seq_handle)

    def __str__(self):
        ret = ""
        for itm in self:
            ret = ret + itm.__str__()
            ret = ret + "\n"

        return ret
