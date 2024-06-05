# vhtquicklist.py - vahatraker (libvht)
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


class VHTQuickList(Iterable):
    """a quick and dirty wrapper for the c int_array"""

    def __init__(self, i, l):
        super(VHTQuickList, self).__init__()
        self._i = i
        self._l = l

    def __len__(self):
        return self._l

    def __iter__(self):
        for itm in range(self._l):
            yield int(self._i[itm])

    def __eq__(self, other):
        if isinstance(other, VHTQuickList):
            for f in range(self._l):
                if self._i[f] != other._i[f]:
                    return False
        elif isinstance(other, list):
            for f in range(self._l):
                if self._i[f] != other[f]:
                    return False
        else:
            return NotImplemented

        return True

    def __getitem__(self, itm):
        if itm >= self._l:
            raise IndexError(itm, "no parrots here")

        if itm < 0:
            raise IndexError(itm, "don't be so negative")

        return int(self._i[itm])

    # this is expensive
    def as_list(self):
        ret = []
        for i in range(self._l):
            ret.append(int(self._i[i]))

        return ret
