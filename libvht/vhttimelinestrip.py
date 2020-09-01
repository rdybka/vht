# vhttimelinestrip.py - Valhalla Tracker (libvht)
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

from libvht import libcvht
from libvht.vhtsequence import VHTSequence


class VHTTimelineStrip:
    def __init__(self, ptr, mod):
        self._ptr = ptr
        self._mod = mod

    def update_strrep(self):
        seq_id = VHTSequence(libcvht.timestrip_get_seq(self._ptr), self._mod).index[1]
        col = libcvht.timestrip_get_col(self._ptr)
        start = libcvht.timestrip_get_start(self._ptr)
        length = libcvht.timestrip_get_length(self._ptr)
        rpb_start = libcvht.timestrip_get_rpb_start(self._ptr)
        rpb_end = libcvht.timestrip_get_rpb_end(self._ptr)

        self._strrep = "%d %d %d %d %d %d" % (
            seq_id,
            col,
            start,
            length,
            rpb_start,
            rpb_end,
        )

    def can_resize(self, l):  # can seq be resized to l?
        return libcvht.timestrip_can_resize_seq(
            self._mod.timeline._tl_handle, self._ptr, l
        )

    def can_rpb(self, rpb):  # can seq's rpb be changed?
        return libcvht.timestrip_can_rpb_seq(
            self._mod.timeline._tl_handle, self._ptr, rpb
        )

    @property
    def prev_id(self):
        seq_ptr = libcvht.timeline_get_prev_seq(
            self._mod.timeline._tl_handle, self._ptr
        )

        if seq_ptr:
            idx = libcvht.sequence_get_index(seq_ptr)
            return 0, idx
        else:
            return self.col

    @property
    def next_id(self):
        seq_ptr = libcvht.timeline_get_next_seq(
            self._mod.timeline._tl_handle, self._ptr
        )
        if seq_ptr:
            idx = libcvht.sequence_get_index(seq_ptr)
            return 0, idx
        else:
            return self.col

    @property
    def seq(self):
        return VHTSequence(
            libcvht.timestrip_get_seq(self._ptr), self._mod, self._mod.cb_new_track
        )

    @property
    def col(self):
        return libcvht.timestrip_get_col(self._ptr)

    @property
    def start(self):
        return libcvht.timestrip_get_start(self._ptr)

    @start.setter
    def start(self, value):
        old = libcvht.timestrip_get_start(self._ptr)
        if old != value:
            libcvht.timestrip_set_start(self._ptr, int(value))
            self._mod.timeline.update()

    @property
    def length(self):
        return libcvht.timestrip_get_length(self._ptr)

    @length.setter
    def length(self, value):
        libcvht.timestrip_set_length(self._ptr, value)
        self._mod.timeline.update()

    @property
    def rpb_start(self):
        return libcvht.timestrip_get_rpb_start(self._ptr)

    @rpb_start.setter
    def rpb_start(self, value):
        libcvht.timestrip_set_rpb_start(self._ptr, value)

    @property
    def rpb_end(self):
        return libcvht.timestrip_get_rpb_end(self._ptr)

    @rpb_start.setter
    def rpb_end(self, value):
        libcvht.timestrip_set_rpb_end(self._ptr, value)

    def __str__(self):
        self.update_strrep()
        return self._strrep
