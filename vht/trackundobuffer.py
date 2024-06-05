# trackundobuffer.py - vahatraker
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

from copy import deepcopy


class TrackUndoBuffer:
    def __init__(self, trk):
        self._trk = trk
        self._states = []
        self._state = {}

        self._states.append({})

    def reset(self):
        self._states = []
        self._state = {}

    def add_state(self, add_if_empty=False):
        state = {}
        for x, c in enumerate(self._trk):
            for y, r in enumerate(c):
                if r.type:
                    state[(x, y)] = (
                        r.type,
                        r.note,
                        r.velocity,
                        r.delay,
                        r.prob,
                        r.velocity_range,
                        r.delay_range,
                    )

        if self._states:
            s = self._state
            for k in s:
                if k in state:
                    if state[k] == s[k]:
                        del state[k]
                else:
                    state[k] = 0

        if state or add_if_empty:
            self._states.append(state)

        for k in state:
            self._state[k] = state[k]
            if state[k] == 0:
                del self._state[k]

    def clone(self, dest):
        dest._states = deepcopy(self._states)
        dest._state = deepcopy(self._state)

    def restore(self):
        if len(self._states) == 1:
            return

        del self._states[-1]

        self._state = {}
        for s in self._states:
            for k in s.keys():
                self._state[k] = s[k]
                if s[k] == 0:
                    del self._state[k]

        cols = 0
        for k in self._state:
            if k[0] > cols:
                cols = k[0]

        cols += 1

        self._trk.clear()
        while len(self._trk) < cols:
            self._trk.add_column()

        for x, c in enumerate(self._trk):
            for y, r in enumerate(c):
                if (x, y) in self._state.keys():
                    r = self._state[(x, y)]
                    if r == 0:
                        self._trk[x][y].clear()
                    else:
                        self._trk[x][y].type = r[0]
                        self._trk[x][y].note = r[1]
                        self._trk[x][y].velocity = r[2]
                        self._trk[x][y].delay = r[3]
                        self._trk[x][y].prob = r[4]
                        self._trk[x][y].velocity_range = r[5]
                        self._trk[x][y].delay_range = r[6]
