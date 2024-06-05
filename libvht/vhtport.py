# vhtport.py - vahatraker (libvht)
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


class VHTPort:
    def __init__(self, clt_handle, name):
        self._clt_handle = clt_handle
        self._name = name
        self._valid = False
        self._prtref = libcvht.midi_get_port_ref(clt_handle, name)
        self._cons = []

        if self._prtref:
            self._valid = True

        if self._valid:
            self.update_strrep()

    def __eq__(self, other):
        if type(other) is str:
            if self._name == other:
                return True
            else:
                return False

        if self._name == other._name:
            return True

        return False

    def update_strrep(self):
        name = self._name

        self._strrep = "[%s][%5s] [%s] %s %s" % (
            "!" if self.physical else " ",
            self.type,
            "*" if self.mine else " ",
            "-->" if self.input else "<--" if self.output else "   ",
            name,
        )

    def connect(self, p2):
        libcvht.midi_port_connect(self._clt_handle, self._name, p2._name)

    def disconnect(self, p2):
        libcvht.midi_port_disconnect(self._clt_handle, self._name, p2._name)

    @property
    def valid(self):
        self._valid = False
        self._prtref = libcvht.midi_get_port_ref(self._clt_handle, self._name)
        if self._prtref:
            self._valid = True

        return self._valid

    @property
    def type(self):
        return libcvht.midi_get_port_type(self._prtref).split()[-1]

    @property
    def input(self):
        return True if libcvht.midi_get_port_input(self._prtref) else False

    @property
    def output(self):
        return True if libcvht.midi_get_port_output(self._prtref) else False

    @property
    def physical(self):
        return True if libcvht.midi_get_port_physical(self._prtref) else False

    @property
    def mine(self):
        return (
            True
            if libcvht.midi_get_port_mine(self._clt_handle, self._prtref)
            else False
        )

    @property
    def connections(self):
        self._cons = []
        c = libcvht.midi_get_port_connections(self._clt_handle, self._prtref)
        if not c:
            return self._cons

        for p in range(libcvht.charpp_nitems(c)):
            self._cons.append(VHTPort(self._clt_handle, libcvht.charpp_item(c, p)))

        libcvht.midi_free_charpp(c)

        return self._cons

    @property
    def name(self):
        return self._name

    @property
    def pname(self):
        pn = libcvht.midi_get_port_pname(self._clt_handle, self._prtref)
        return pn if pn else self._name

    def __str__(self):
        self.update_strrep()
        return self._strrep
