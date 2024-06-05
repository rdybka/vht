# vhttimelinechange.py - vahatraker (libvht)
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

from libvht import libcvht


class VHTTimelineChange:
    def __init__(self, tl, chg):
        self._tl_handle = tl
        self._chg_handle = chg

    def __eq__(self, other):
        if type(other) is not type(self):
            return False

        if self.row == other.row:
            return True

        return False

    @property
    def bpm(self):
        return libcvht.timechange_get_bpm(self._chg_handle)

    @bpm.setter
    def bpm(self, val):
        libcvht.timechange_set_bpm(self._tl_handle, self._chg_handle, val)

    @property
    def linked(self):
        return libcvht.timechange_get_linked(self._chg_handle)

    @linked.setter
    def linked(self, val):
        libcvht.timechange_set_linked(
            self._tl_handle, self._chg_handle, val if val == 0 else 1
        )

    @property
    def row(self):
        return libcvht.timechange_get_row(self._chg_handle)

    @row.setter
    def row(self, val):
        libcvht.timechange_set_row(self._tl_handle, self._chg_handle, int(val))

    def __str__(self):
        ret = {"bpm": self.bpm, "linked": self.linked, "row": self.row}

        return repr(ret)
