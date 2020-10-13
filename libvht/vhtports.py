# vhtports.py - Valhalla Tracker (libvht)
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
from libvht.vhtport import VHTPort


class VHTPorts(Iterable):
    def __init__(self, clt_handle):
        super(VHTPorts, self).__init__()
        self._clt_handle = clt_handle

    def refresh(self):
        libcvht.midi_refresh_port_names(self._clt_handle)

    def __len__(self):
        return libcvht.midi_nport_names(self._clt_handle)

    def __iter__(self):
        for itm in range(self.__len__()):
            yield VHTPort(
                self._clt_handle, libcvht.midi_get_port_name(self._clt_handle, itm)
            )

    def __getitem__(self, itm):
        if 0 > itm >= self.__len__():
            raise IndexError(itm)

        return VHTPort(
            self._clt_handle, libcvht.midi_get_port_name(self._clt_handle, itm)
        )

    def __str__(self):
        ret = ""
        for n, p in enumerate(self):
            ret += "%2d: %s\n" % (n, p)

        return ret
