# codedaemon.py - vahatraker
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

# after long consideration, it all runs in tick
# no threading involved

import traceback

default_code = """def on_row(seq, row):
    if not seq.playing:
        return

    if row % 3 == 0:
        print(seq.index, row)
"""


class CodeDaemon:
    def __init__(self):
        self._last_code = {}
        self._errs = {}
        self._compiled = {}
        self._running = []
        self._run = []
        self._lastrow = {}

    def __del__(self):
        self._run.clear()
        self._running.clear()

    def tick(self):
        for s in self._running:
            lrow = -1
            if s in self._lastrow:
                lrow = self._lastrow[s]
            nr = s.next_row
            if nr != lrow:
                if s in self._compiled:
                    try:
                        kod = self._compiled[s]
                        kod(s, nr)
                    except Exception:
                        self._errs[s] = traceback.format_exc(0)
                        print(self._errs[s])
                        self._run.remove(s)

                self._lastrow[s] = nr

        self.update_threads()

    def update_threads(self):
        for r in self._run:
            if not r in self._running:
                self._running.append(r)

        torem = []
        for r in self._running:
            if not r in self._run:
                torem.append(r)

        for r in torem:
            self._running.remove(r)

    def post_code(self, seq, code):
        self._errs[seq] = None

        if seq in self._last_code:
            if code == self._last_code[seq] and seq in self._compiled:
                return 0

        if seq in self._compiled:
            del self._compiled[seq]

        try:
            c = compile(code, "seq%d" % (seq.__hash__()), "exec")
            loc = {}
            exec(c, globals(), loc)
            if "on_row" in loc:
                self._compiled[seq] = loc["on_row"]
            else:
                raise Exception("No on_row defined")
        except Exception:
            self._errs[seq] = traceback.format_exc(0)
            return self._errs[seq]

        self._last_code[seq] = code
        if seq in self._run:
            self._run.remove(seq)

        return 0

    def run(self, seq, val):
        if val:
            if not seq in self._run:
                self._run.append(seq)
        else:
            if seq in self._run:
                self._run.remove(seq)

        self.update_threads()

    def want_run(self, seq):
        if seq in self._run:
            return True
        else:
            return False

    def remove_seq(self, seq):
        if seq in self._last_code:
            del self._last_code[seq]

        if seq in self._compiled:
            del self._compiled[seq]

        if seq in self._run:
            self._run.remove(seq)

        if seq in self._running:
            self._running.remove(seq)

    @property
    def def_code(self):
        return default_code

    def err(self, seq):
        if seq in self._errs:
            return self._errs[seq]
        else:
            return None
