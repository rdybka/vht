# vhttimelinechange.py - Valhalla Tracker (libvht)
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


class VHTTimelineChange:
    def __init__(self, tl, chg):
        self._tl_handle = tl
        self._chg_handle = chg

    @property
    def bpm(self):
        return libcvht.timechange_get_bpm(self._chg_handle)

    @property
    def linked(self):
        return libcvht.timechange_get_linked(self._chg_handle)

    @property
    def row(self):
        return libcvht.timechange_get_row(self._chg_handle)

    def __str__(self):
        ret = {"bpm": self.bpm, "linked": self.linked, "row": self.row}

        return repr(ret)
