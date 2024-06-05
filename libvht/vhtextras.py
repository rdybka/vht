# vhtextras.py - vahatraker (libvht)
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

from collections.abc import MutableMapping

import json


class VHTExtras(MutableMapping):
    """A dict that keeps it's json copy depp in vht guts.
    This will allow gui to keep settings irrelevant to
    sequencer engine inside stuff we clone.
    Ripped off a very nice template on stackoverflow
    """

    def __init__(self, func_get, func_set):
        self._store = None
        self._func_get = func_get
        self._func_set = func_set

        self.read()

    @property
    def jsn(self):
        return self._func_get()

    @jsn.setter
    def jsn(self, val):
        self._func_set(val)
        self.read()

    def read(self):
        s = self._func_get()
        if s:
            self._store = json.loads(s)
        else:
            self._store = dict()

    def write(self):
        self._func_set(json.dumps(self._store))

    def __getitem__(self, key):
        return self._store[str(key)]

    def __setitem__(self, key, value):
        self._store[str(key)] = value
        self.write()

    def __delitem__(self, key):
        del self._store[key]
        self.write()
        self.read()

    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)
