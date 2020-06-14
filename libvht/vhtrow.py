# vhtrow.py - Valhalla Tracker (libvht)
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

from libvht import libcvht


class VHTRow:
    def __init__(self, rowptr):
        self._rowptr = rowptr

        self._type = libcvht.row_get_type(self._rowptr)
        self._note = libcvht.row_get_note(self._rowptr)
        self._velocity = libcvht.row_get_velocity(self._rowptr)
        self._delay = libcvht.row_get_delay(self._rowptr)
        self.update_strrep()

    def __eq__(self, other):
        if self._type != other._type:
            return False
        if self._note != other._note:
            return False
        if self._velocity != other._velocity:
            return False
        if self._delay != other._delay:
            return False

        return True

    def update_strrep(self):
        notes = ["C-", "C#", "D-", "D#", "E-", "F-", "F#", "G-", "G#", "A-", "A#", "B-"]
        note = self._note % 12
        octave = (self._note // 12) - 1
        if self._type == 1:  # note_on
            if octave < 10:
                if octave == -1:
                    self._strrep = notes[note] + "<"
                else:
                    self._strrep = notes[note] + str(octave)
            else:
                self._strrep = notes[note] + "A"
            return

        if self._type == 2:  # note_off
            self._strrep = "  ==="
            return

        self._strrep = "---"

    def copy(self, row):
        self._type = row._type
        self._note = row._note
        self._velocity = row._velocity
        self._delay = row._delay
        libcvht.row_set(
            self._rowptr, self._type, self._note, self._velocity, self._delay
        )
        self.update_strrep()

    def clear(self):
        self._type = 0
        self._note = 0
        self._velocity = 0
        self._delay = 0
        libcvht.row_set(self._rowptr, 0, 0, 0, 0)
        self.update_strrep()

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        self._type = value
        libcvht.row_set_type(self._rowptr, self._type)

    @property
    def note(self):
        return self._note

    @note.setter
    def note(self, value):
        if isinstance(value, int):
            self._note = value
            libcvht.row_set_note(self._rowptr, self._note)

        if isinstance(value, str):
            self._note = libcvht.parse_note(value)
            libcvht.row_set_note(self._rowptr, self._note)
            self.type = 1
            if self.velocity == 0:
                self.velocity = 100

        self.update_strrep()

    @property
    def velocity(self):
        return self._velocity

    @velocity.setter
    def velocity(self, value):
        self._velocity = int(value)
        libcvht.row_set_velocity(self._rowptr, self._velocity)

    @property
    def delay(self):
        return self._delay

    @delay.setter
    def delay(self, value):
        self._delay = int(value)
        libcvht.row_set_delay(self._rowptr, self._delay)

    def __str__(self):
        return self._strrep
