# poormanspiano.py - Valhalla Tracker
#
# Copyright (C) 2019 Remigiusz Dybka - remigiusz.dybka@gmail.com
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

from vht import cfg, mod
from gi.repository import Gdk
import math
import gi

gi.require_version("Gtk", "3.0")


class PoorMansPiano:
    def __init__(self, trk, seq):
        self.seq = seq
        self.trk = trk
        self.notes = {
            122: "c",
            115: "c#",
            120: "d",
            100: "d#",
            99: "e",
            118: "f",
            103: "f#",
            98: "g",
            104: "g#",
            110: "a",
            106: "a#",
            109: "b",
        }
        self.notes2 = {
            113: "c",
            50: "c#",
            119: "d",
            51: "d#",
            101: "e",
            114: "f",
            53: "f#",
            116: "g",
            54: "g#",
            121: "a",
            55: "a#",
            117: "b",
        }

        self.mnotes = [122, 115, 120, 100, 99, 118, 103, 98, 104, 110, 106, 109]
        self.mnotes2 = [113, 50, 119, 51, 101, 114, 53, 116, 54, 121, 55, 117]

        self.note_on = None
        self.mnotes.append(self.mnotes)
        self.ringing = []

    def silence(self):
        for n in self.ringing:
            self.ringing.remove(n)
            mod.sneakily_queue_midi_note_off(
                self.seq._seq_handle, self.trk.port, self.trk.channel, n
            )

        self.note_on = None

    def key2ctrl(self, key, ctrl, off=False):
        f = cfg.velocity_keys.find(Gdk.keyval_name(key))
        val = -1
        if f > -1:
            val = int(f * (127 / (len(cfg.velocity_keys) - 1)))

        if f == 0:
            val = 0

        if f == len(cfg.velocity_keys) - 1:
            val = 127

        if f == math.floor(len(cfg.velocity_keys) / 2):
            val = 64

        if val > -1:
            if not off:
                mod.sneakily_queue_midi_ctrl(
                    self.seq._seq_handle, self.trk._trk_handle, val, ctrl
                )
            return True

        return False

    def key2note(self, key, note_off=False):
        mnt = -23
        if key in self.mnotes:
            mnt = self.mnotes.index(key)

        if key in self.mnotes2:
            mnt = self.mnotes2.index(key) + 12

        if mnt == -23:
            return None

        mnt += cfg.octave * 12
        while mnt > 127:
            mnt -= 12

        if not note_off:
            if self.note_on != mnt:
                mod.sneakily_queue_midi_note_on(
                    self.seq._seq_handle,
                    self.trk.port,
                    self.trk.channel,
                    mnt,
                    cfg.velocity,
                )
                self.note_on = mnt
                self.ringing.append(mnt)
        else:
            self.note_on = None
            mod.sneakily_queue_midi_note_off(
                self.seq._seq_handle, self.trk.port, self.trk.channel, mnt
            )
            while mnt in self.ringing:
                self.ringing.remove(mnt)

        octave = cfg.octave
        if key in self.notes:
            return "%s%d" % (self.notes[key], octave)

        octave = cfg.octave
        octave += 1
        if octave > 8:
            octave = 8
        if key in self.notes2:
            return "%s%d" % (self.notes2[key], octave)
        return None
