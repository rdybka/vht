# vhtctrlrow.py - vahatraker (libvht)
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


class VHTCtrlRow:
    def __init__(self, crowptr, dummy=False):
        self._crowptr = crowptr
        self._dummy = dummy

        self._velocity = libcvht.ctrlrow_get_velocity(self._crowptr)
        self._linked = libcvht.ctrlrow_get_linked(self._crowptr)
        self._smooth = libcvht.ctrlrow_get_smooth(self._crowptr)
        self._anchor = libcvht.ctrlrow_get_anchor(self._crowptr)

        self.update_strrep()

    def __eq__(self, other):
        if other is None:
            return False

        if self._velocity != other._velocity:
            return False
        if self._linked != other._linked:
            return False
        if self._linked != other._smooth:
            return False
        if self._anchor != other._anchor:
            return False

        return True

    def update_strrep(self):
        lnk = " "
        if self._linked == 1:
            lnk = "L"

        if self._velocity > -1:
            self._strrep = "%3d %s %d %d" % (
                self._velocity,
                lnk,
                self._smooth,
                self._anchor,
            )
        else:
            self._strrep = "--- - - -"

    def copy(self, row):
        self._velocity = row._velocity
        self._linked = row._linked
        self._smooth = row._smooth
        self._anchor = row._anchor
        if not self._dummy:
            libcvht.ctrlrow_set(
                self._crowptr, self._velocity, self._linked, self._smooth, self.anchor
            )
        self.update_strrep()

    def clear(self):
        self._velocity = -1
        self._linked = 0
        self._smooth = 0
        self._anchor = 0
        if not self._dummy:
            libcvht.ctrlrow_set(self._crowptr, -1, 0, 0, 0)
        self.update_strrep()

    def dummy(self):
        return VHTCtrlRow(self._crowptr, True)

    @property
    def velocity(self):
        return self._velocity

    @velocity.setter
    def velocity(self, value):
        self._velocity = int(value)

        if not self._dummy:
            libcvht.ctrlrow_set_velocity(self._crowptr, self._velocity)

    @property
    def linked(self):
        return self._linked

    @linked.setter
    def linked(self, value):
        self._linked = int(value)
        if not self._dummy:
            libcvht.ctrlrow_set_linked(self._crowptr, self._linked)

    @property
    def smooth(self):
        return self._smooth

    @smooth.setter
    def smooth(self, value):
        self._smooth = int(value)
        if not self._dummy:
            libcvht.ctrlrow_set_smooth(self._crowptr, self._smooth)

    @property
    def anchor(self):
        return self._anchor

    @anchor.setter
    def anchor(self, value):
        self._anchor = int(value)
        if not self._dummy:
            libcvht.ctrlrow_set_anchor(self._crowptr, self._anchor)

    def __str__(self):
        return self._strrep
