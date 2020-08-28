# vhttimelinestrips.py - Valhalla Tracker (libvht)
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
from libvht import libcvht
from libvht.vhttimelinestrip import VHTTimelineStrip
from libvht.vhtsequence import VHTSequence


class VHTTimelineStrips(Iterable):
    def __init__(self, mod, tl):
        super(VHTTimelineStrips, self).__init__()
        self._tl_handle = tl
        self._mod_handle = mod._mod_handle
        self._mod = mod

    def __len__(self):
        return libcvht.timeline_get_nstrips(self._tl_handle)

    def __iter__(self):
        for itm in range(self.__len__()):
            yield VHTTimelineStrip(
                libcvht.timeline_get_strip(self._tl_handle, itm), self._mod
            )

    def __getitem__(self, itm):
        if 0 > itm >= self.__len__():
            raise IndexError(itm)

        return VHTTimelineStrip(
            libcvht.timeline_get_strip(self._tl_handle, itm), self._mod
        )

    def get_seq(self, itm):
        sq = libcvht.timeline_get_seq(self._tl_handle, itm)
        if sq:
            return VHTSequence(sq, self._mod, self._mod.cb_new_track)
        else:
            return None

    def insert(self, col, seq, start, length, rpb_start, rpb_end):
        return VHTTimelineStrip(
            libcvht.timeline_add_strip(
                self._tl_handle, col, seq, start, length, rpb_start, rpb_end,
            ),
            self._mod,
        )

    def insert_parent(self, seq_id, start, length, rpb_start, rpb_end):
        ns = libcvht.sequence_clone(libcvht.module_get_seq(self._mod_handle, seq_id))

        return VHTTimelineStrip(
            libcvht.timeline_add_strip(
                self._tl_handle, seq_id, ns, start, length, rpb_start, rpb_end,
            ),
            self._mod,
        )

    def insert_clone(self, strp_id):
        srcstr = self[strp_id]
        ns = libcvht.sequence_clone(
            libcvht.timeline_get_seq(self._tl_handle, int(strp_id))
        )
        pos = libcvht.timeline_place_clone(self._tl_handle, int(strp_id))

        return VHTTimelineStrip(
            libcvht.timeline_add_strip(
                self._tl_handle,
                srcstr.col,
                ns,
                pos,
                srcstr.length,
                srcstr.rpb_start,
                srcstr.rpb_end,
            ),
            self._mod,
        )

    def delete(self, itm):
        libcvht.timeline_del_strip(self._tl_handle, itm)
        libcvht.timeline_update(self._tl_handle)
