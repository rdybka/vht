# vhttimeline.py - Valhalla Tracker (libvht)
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

from libvht.vhttimelinechanges import VHTTimelineChanges
from libvht.vhttimelineticks import VHTTimelineTicks


class VHTTimeline:
    def __init__(self, vht, mod):
        self._mod_handle = mod
        self._vht_handle = vht

        self._tl_handle = self._vht_handle.module_get_timeline(self._mod_handle)
        self.changes = VHTTimelineChanges(self._vht_handle, self._tl_handle)
        self.ticks = VHTTimelineTicks(self._vht_handle, self._tl_handle)

    def __str__(self):
        return "dupa"
        # ret = ""
        # for r in range(self.__len__()):
        # 	ret = ret + str(self[r])
        # 	ret = ret + "\n"
        # return ret
