# trackviewpointer.py - vahatraker
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

from libvht.vhtsequence import VHTSequence
from libvht.vhttrack import VHTTrack

from vht.pulsar import Pulsar
from vht import cfg, mod
import cairo
import gi

gi.require_version("Gtk", "3.0")


class TrackviewPointer:
    def __init__(self, parent, trk, seq):
        self.trk = trk
        if not trk:
            self.trk = seq

        self.seq = seq

        self.spacing = 1.0
        self.opacity = cfg.pointer_opacity
        self._parent = parent
        self.height = cfg.seq_font_size

        self.lpos = None

        self.pulse = Pulsar(seq.rpb)

        self.stopped = False

    def draw(self, pos):
        self.pulse.freq = mod[mod.curr_seq].rpb

        if isinstance(self.trk, VHTTrack):
            if mod[mod.curr_seq].playing == 0:
                if self.stopped:
                    return

                self._parent.reblit()
                self.stopped = True
                return

        self.stopped = False

        w = self._parent.get_allocated_width()

        self.height = self._parent.parent.font_size

        cr = self._parent._context

        y = pos - 1
        if y < 0:
            y = 0

        if self.lpos:
            self._parent.reblit(self.lpos - 2, self.lpos)

        self._parent.reblit(pos - 2, pos)
        self.lpos = pos

        y = pos * self._parent.txt_height
        y -= self.height / 2.0

        r = int(self.trk.pos)

        # sideview
        if isinstance(self.trk, VHTSequence):
            if self.seq.pos > self.seq.length:
                return

            i = 0.5
            if r % self.seq.rpb == 0:
                i *= 2

            x = 0
            xx = (self._parent.txt_width / 4.0) * 3.1

            cl = cfg.colour
            if mod.record == 2:
                cl = cfg.record_colour
                i = self.pulse.intensity(mod[mod.curr_seq].pos)

            gradient = cairo.LinearGradient(x, y, x, y + self.height)
            gradient.add_color_stop_rgba(0.0, *(col * i for col in cl), 0)
            gradient.add_color_stop_rgba(
                0.5 - cfg.pointer_width / 2, *(col * i for col in cl), 0
            )
            gradient.add_color_stop_rgba(0.5, *(col * i for col in cl), self.opacity)
            gradient.add_color_stop_rgba(
                0.5 + cfg.pointer_width / 2, *(col * i for col in cl), 0
            )
            gradient.add_color_stop_rgba(1.0, *(col * i for col in cl), 0)
            cr.set_source(gradient)

            # if type(mod.curr_seq) is int:
            cr.rectangle(x, y, xx, self.height)
            cr.fill()
            # else:
            #    pass  # pointer for strip

            return

        r = int(self.trk.pos)
        if r < 0 or r >= self.trk.nrows:
            return

        if self._parent.show_notes:
            xtraoffs = 0
            for c in range(len(self.trk)):
                i = 0.5
                if r % self.seq.rpb == 0:
                    i *= 1.0

                rw = self.trk[c][r]

                lp = self.trk.get_last_row_played(c)

                if (
                    lp > -1
                    and lp < self.trk.nrows
                    and self.trk[c][lp].type == 1
                    and abs(r - lp) <= 1
                ):
                    i *= 1.5 + 2.0 * (self.trk.pos - r)

                x = c * self._parent.txt_width + xtraoffs
                xx = self._parent.txt_width

                ed = self._parent.velocity_editor
                if ed and c == ed.col:
                    xx = ed.x_from
                    xtraoffs += ed.width

                ed = self._parent.timeshift_editor
                if ed and c == ed.col:
                    xx = ed.x_from
                    xtraoffs += ed.width

                ed = self._parent.prob_editor
                if ed and c == ed.col:
                    xx = ed.x_from
                    xtraoffs += ed.width

                cl = cfg.colour
                if mod.active_track:
                    if mod.active_track.trk.index == self.trk.index and mod.record == 1:
                        cl = cfg.record_colour
                        i = self.pulse.intensity(pos)

                gradient = cairo.LinearGradient(x, y, x, y + self.height)
                gradient.add_color_stop_rgba(0.0, *(col * i for col in cl), 0)
                gradient.add_color_stop_rgba(
                    0.5 - cfg.pointer_width / 2, *(col * i for col in cl), 0
                )
                gradient.add_color_stop_rgba(
                    0.5, *(col * i for col in cl), self.opacity
                )
                gradient.add_color_stop_rgba(
                    0.5 + cfg.pointer_width / 2, *(col * i for col in cl), 0
                )
                gradient.add_color_stop_rgba(1.0, *(col * i for col in cl), 0)

                cr.set_source(gradient)
                cr.rectangle(x, y, xx, self.height)
                cr.fill()

        if self._parent.show_pitchwheel or self._parent.show_controllers:
            for c in range(self.trk.nctrl):
                v = self.trk.get_lctrlval(c)

                draw = True
                if c == 0 and not self._parent.show_pitchwheel:
                    draw = False

                x = 0
                xx = 0
                if c > len(self._parent.controller_editors):
                    break

                if c == 0:
                    x = self._parent.pitchwheel_editor.x_from
                    xx = self._parent.pitchwheel_editor.x_to - x
                else:
                    x = self._parent.controller_editors[c - 1].x_from
                    xx = self._parent.controller_editors[c - 1].x_to - x

                cl = cfg.colour
                if mod.active_track:
                    if mod.active_track.trk.index == self.trk.index and mod.record == 1:
                        cl = cfg.record_colour

                i = 0.5

                gradient = cairo.LinearGradient(x, y, x, y + self.height)
                gradient.add_color_stop_rgba(0.0, *(col * i for col in cl), 0)
                gradient.add_color_stop_rgba(
                    0.5 - cfg.pointer_width / 2, *(col * i for col in cl), 0
                )
                gradient.add_color_stop_rgba(
                    0.5, *(col * i for col in cl), self.opacity
                )
                gradient.add_color_stop_rgba(
                    0.5 + cfg.pointer_width / 2, *(col * i for col in cl), 0
                )
                gradient.add_color_stop_rgba(1.0, *(col * i for col in cl), 0)

                if draw:
                    cr.set_source(gradient)
                    cr.rectangle(x, y, xx, self.height)
                    cr.fill()

                xw = 0

                if c == 0:
                    xw = self._parent.pitchwheel_editor.x_to - (
                        self._parent.pitchwheel_editor.x_from
                        + self._parent.pitchwheel_editor.txt_width
                    )

                    xx = (v / 127) - 64
                    xx = xx * ((xw / 2) / 64)
                    x0 = (
                        self._parent.pitchwheel_editor.x_from
                        + self._parent.pitchwheel_editor.txt_width
                        + (xw / 2)
                    )

                    if v == -1:
                        xx = 0

                    if x0 + xx > self._parent.pitchwheel_editor.x_to:
                        xx = self._parent.pitchwheel_editor.x_to - x0
                else:
                    xw = self._parent.controller_editors[c - 1].x_to - (
                        self._parent.controller_editors[c - 1].x_from
                        + self._parent.controller_editors[c - 1].txt_width
                    )

                    xx = v
                    xx = xx * ((xw / 2) / 64)
                    x0 = (
                        self._parent.controller_editors[c - 1].x_from
                        + self._parent.controller_editors[c - 1].txt_width
                    )
                    if v == -1:
                        xx = 0

                    if x0 + xx > self._parent.controller_editors[c - 1].x_to:
                        xx = self._parent.controller_editors[c - 1].x_to - x0

                if draw:
                    cr.set_source_rgb(
                        *(col * cfg.intensity_txt_highlight for col in cfg.colour)
                    )
                    cr.rectangle(x0, y + (self.height / 2) - 1, xx, 2)
                    cr.fill()
