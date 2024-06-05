# pulsar.py - vahatraker
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


class Pulsar:
    def __init__(self, freq):
        self._freq = freq

    @property
    def freq(self):
        return self._freq

    @freq.setter
    def freq(self, f):
        self._freq = f

    def intensity(self, pos):
        r = 0.8 - ((pos % self._freq) / self._freq)
        return max(r, 0.0)
