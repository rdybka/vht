# poormanspiano.py - vahatraker
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

from vht import cfg, mod
from gi.repository import Gdk
import math
import gi

gi.require_version("Gtk", "3.0")


class PoorMansPiano:
    def __init__(self, trk, seq):
        self.seq = seq
        self.trk = trk

        ape_pattern = "wbwbwwbwbwbw"
        wk = cfg.piano_white_keys
        bk = cfg.piano_black_keys
        if len(wk + bk) == len(ape_pattern) * 2:
            self.mnotes = []

            offsw = 0
            offsb = 0
            for c in ape_pattern * 2:
                k = wk[offsw]
                offsw += 1
                if c == "b":
                    k = bk[offsb]
                    offsb += 1
                    offsw -= 1

                self.mnotes.append(Gdk.unicode_to_keyval(ord(k)))
        else:
            self.mnotes = [
                122,
                115,
                120,
                100,
                99,
                118,
                103,
                98,
                104,
                110,
                106,
                109,
                113,
                50,
                119,
                51,
                101,
                114,
                53,
                116,
                54,
                121,
                55,
                117,
            ]

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
        if not key:
            return False

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
                self.trk.indicators = self.trk.indicators | 8

                if mod.gui_midi_capture:
                    mod.sneakily_queue_midi_in(self.trk.channel, 4, ctrl, val)
            return True

        if key in self.mnotes:
            return True

        return False

    def key2note(self, key, note_off=False):
        mnt = -23

        if key in self.mnotes:
            mnt = self.mnotes.index(key)

        if mnt == -23:
            return -1

        mnt += cfg.octave * 12
        mnt = min(mnt, 127)

        if not note_off:
            if self.note_on != mnt:
                mod.sneakily_queue_midi_note_on(
                    self.seq._seq_handle,
                    self.trk.port,
                    self.trk.channel,
                    mnt,
                    int(cfg.velocity),
                )

                if mod.gui_midi_capture:
                    mod.sneakily_queue_midi_in(
                        self.trk.channel, 1, mnt, int(cfg.velocity)
                    )

                self.note_on = mnt
                self.ringing.append(mnt)
                self.trk.indicators = self.trk.indicators | 5
        else:
            self.note_on = None
            mod.sneakily_queue_midi_note_off(
                self.seq._seq_handle, self.trk.port, self.trk.channel, mnt
            )
            self.trk.indicators = self.trk.indicators | 5
            while mnt in self.ringing:
                self.ringing.remove(mnt)

        return mnt

    def k2n(self, key):
        mnt = -23

        if key in self.mnotes:
            mnt = self.mnotes.index(key)

        if mnt == -23:
            return -1

        mnt += cfg.octave * 12
        mnt = min(mnt, 127)

        return mnt
