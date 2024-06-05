# vhttimelineloop.py - vahatraker (libvht)
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


class VHTTimelineLoop:
    def __init__(self, tl):
        self._tl_handle = tl

    @property
    def active(self):
        return True if libcvht.timeline_get_loop_active(self._tl_handle) else False

    @active.setter
    def active(self, val):
        if val:
            libcvht.timeline_set_loop_active(self._tl_handle, 1)
        else:
            libcvht.timeline_set_loop_active(self._tl_handle, 0)

    @property
    def start(self):
        return libcvht.timeline_get_loop_start(self._tl_handle)

    @start.setter
    def start(self, val):
        libcvht.timeline_set_loop_start(self._tl_handle, int(val))

    @property
    def end(self):
        return libcvht.timeline_get_loop_end(self._tl_handle)

    @end.setter
    def end(self, val):
        libcvht.timeline_set_loop_end(self._tl_handle, int(val))

    def __str__(self):
        return "%d %d %s" % (self.start, self.end, self.active)
