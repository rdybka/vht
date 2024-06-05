# vhttracy.py - vahatraker (libvht)
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


class VHTTracy:
    def __init__(self, trc):
        self._trc_handle = trc

    @property
    def pos(self):
        return libcvht.tracy_get_pos(self._trc_handle)

    @property
    def disp(self):
        return libcvht.tracy_get_disp(self._trc_handle)

    @property
    def tail(self):
        return libcvht.tracy_get_tail(self._trc_handle)

    @property
    def speed(self):
        return libcvht.tracy_get_speed(self._trc_handle)

    @speed.setter
    def speed(self, v):
        libcvht.tracy_set_speed(self._trc_handle, float(v))

    @property
    def scale(self):
        return libcvht.tracy_get_scale(self._trc_handle)

    @scale.setter
    def scale(self, s):
        libcvht.tracy_set_scale(self._trc_handle, float(s))

    @property
    def phase(self):
        return libcvht.tracy_get_phase(self._trc_handle)

    @phase.setter
    def phase(self, v):
        libcvht.tracy_set_phase(self._trc_handle, float(v))

    @property
    def mult(self):
        return libcvht.tracy_get_mult(self._trc_handle)

    @mult.setter
    def mult(self, v):
        libcvht.tracy_set_mult(self._trc_handle, float(v))

    @property
    def zoom(self):
        return libcvht.tracy_get_zoom(self._trc_handle)

    @zoom.setter
    def zoom(self, z):
        libcvht.tracy_set_zoom(self._trc_handle, float(z))

    @property
    def qnt(self):
        return libcvht.tracy_get_qnt(self._trc_handle)

    @qnt.setter
    def qnt(self, q):
        libcvht.tracy_set_qnt(self._trc_handle, int(q))
