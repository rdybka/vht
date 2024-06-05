# vhttimelinechanges.py - vahatraker (libvht)
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

from collections.abc import Iterable
from libvht.vhttimelinechange import VHTTimelineChange
from libvht import libcvht


class VHTTimelineChanges(Iterable):
    def __init__(self, tl):
        super(VHTTimelineChanges, self).__init__()
        self._tl_handle = tl

    def __len__(self):
        return libcvht.timeline_get_nchanges(self._tl_handle)

    def __iter__(self):
        for itm in range(self.__len__()):
            yield VHTTimelineChange(
                self._tl_handle, libcvht.timeline_get_change(self._tl_handle, itm)
            )

    def __getitem__(self, itm):
        if itm >= self.__len__():
            raise IndexError()

        if itm < 0:
            raise IndexError()

        return VHTTimelineChange(
            self._tl_handle, libcvht.timeline_get_change(self._tl_handle, itm)
        )

    def insert(self, bpm, row, linked):
        return VHTTimelineChange(
            self._tl_handle,
            libcvht.timeline_add_change(
                self._tl_handle, float(bpm), int(row), int(linked)
            ),
        )

    def __delitem__(self, itm):
        if itm >= self.__len__():
            raise IndexError()

        if itm < 0:
            raise IndexError()

        libcvht.timechange_del(self._tl_handle, itm)

    def get_at_qb(self, qb, tol=0):
        tc = libcvht.timeline_change_get_at(self._tl_handle, int(qb), int(tol))
        return VHTTimelineChange(self._tl_handle, tc) if tc else None
