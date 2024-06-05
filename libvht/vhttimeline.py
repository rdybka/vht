# vhttimeline.py - vahatraker (libvht)
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

from libvht.vhttimelinechanges import VHTTimelineChanges
from libvht.vhttimelineticks import VHTTimelineTicks
from libvht.vhttimelinestrips import VHTTimelineStrips
from libvht.vhttimelineloop import VHTTimelineLoop
from libvht import libcvht


class VHTTimeline:
    def __init__(self, mod):
        self._mod_handle = mod._mod_handle
        self._mod = mod

        self._tl_handle = libcvht.module_get_timeline(self._mod_handle)
        self.strips = VHTTimelineStrips(self._mod, self._tl_handle)
        self.ticks = VHTTimelineTicks(self._tl_handle)
        self.changes = VHTTimelineChanges(self._tl_handle)
        self.loop = VHTTimelineLoop(self._tl_handle)

    def clear(self):
        libcvht.timeline_clear(self._tl_handle)

    @property
    def length(self):  # in seconds
        return libcvht.timeline_get_length(self._tl_handle)

    @property
    def nqb(self):  # length in qbeats
        return libcvht.timeline_get_nticks(self._tl_handle)

    @property
    def pos(self):
        return libcvht.timeline_get_pos(self._tl_handle)

    @pos.setter
    def pos(self, val):
        libcvht.timeline_set_pos(self._tl_handle, float(val), 0)

    def t2qb(self, t):  # qb for time in seconds
        return libcvht.timeline_get_qb(self._tl_handle, t)

    def qb2t(self, qb):  # time is seconds for given qb
        return libcvht.timeline_get_qb_time(self._tl_handle, qb)

    def qb2s(self, col, qb):  # strip_id (if any) for given col and qb
        return libcvht.timeline_get_strip_for_qb(self._tl_handle, col, int(qb))

    def last_strip(self, col, qb):  # last strip (if any) for given col and qb
        ls = libcvht.timeline_get_last_strip(self._tl_handle, col, int(qb))
        if ls > -1:
            return self.strips[ls]
        else:
            return None

    def bpm_at_qb(self, qb):
        return libcvht.timeline_get_bpm_at_qb(self._tl_handle, int(qb))

    def interpol_at_qb(self, qb):  # is the bpm interpolated at this point?
        return (
            True
            if libcvht.timeline_get_interpol_at_qb(self._tl_handle, int(qb))
            else False
        )

    def expand_start(
        self, qb_start
    ):  # prepare strips for expanding, returns max retract value
        return libcvht.timeline_expand_start(self._tl_handle, int(qb_start))

    def expand(self, qb_start, qb_n):
        return libcvht.timeline_expand(self._tl_handle, int(qb_start), int(qb_n))

    def room_at(self, col, qb, ig=-1):  # nqb free after qb (-1 - unl)
        return libcvht.timeline_get_room(self._tl_handle, col, int(qb), int(ig))

    def place_clone(self, strip_id):  # first free qb for a clone of strip_id
        return libcvht.timeline_place_clone(self._tl_handle, int(strip_id))

    def snap(self, strip_id, delta):  # new position snapped against others
        return libcvht.timeline_get_snap(self._tl_handle, strip_id, int(delta))

    def update(self):
        libcvht.timeline_update(self._tl_handle)

    def __str__(self):
        return "dupa"
