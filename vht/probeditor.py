# probeditor.py - vahatraker
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

from vht import cfg

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk


class ProbEditor:
    def __init__(self, tv, col, row, event):
        self.col = col
        self.row = row
        self.tv = tv
        self.event_y = event.y

        self.trk = tv.trk

        self.confirmed = False
        self.clearing = False
        self.lock = False
        self.locked = self.trk[col][row].prob
        self.start_value = self.locked
        self.line = -1
        self.hover_row = -1
        self.hover_prob = -1

        self.x_from = 0
        self.x_to = 0
        self.width = 100

    def precalc(self, cr):
        (x, y, width, height, dx, dy) = cr.text_extents("0")
        self.width = max((cfg.timeshift_editor_char_width * width), 100)
        fld = 3
        if self.tv.show_timeshift:
            fld += 1

        self.x_from = self.tv.txt_width * self.col + self.tv.fld_width * fld - dx / 2
        self.x_to = self.width

        if self.col == len(self.trk) - 1:
            self.width += dx / 2

    def draw(self, cr, col, r, rw):
        yh = cfg.editor_row_height * self.tv.txt_height
        yp = (self.tv.txt_height - yh) / 2.0

        if rw.type == 1 or rw.type == 2:
            cr.set_line_width(1.0)
            cr.set_source_rgba(*(col * cfg.intensity_txt for col in cfg.colour), 1)
            cr.rectangle(
                self.x_from + ((self.x_to / 100) * (rw.prob)),
                r * self.tv.txt_height + yp,
                self.x_to - ((self.x_to / 100) * (rw.prob)),
                yh,
            )
            cr.fill()

            cr.set_source_rgba(*(col * cfg.intensity_txt for col in cfg.colour), 1)
            cr.rectangle(self.x_from, r * self.tv.txt_height + yp, self.x_to, yh)
            cr.stroke()

        if self.line > -1:
            cr.set_source_rgba(*(col * cfg.intensity_txt for col in cfg.colour), 1)
            cr.move_to(
                self.x_from
                + (self.x_to / 100.0) * self.tv.trk[self.col][self.line].prob,
                self.line * self.tv.txt_height + yp,
            )
            cr.line_to(
                self.x_from + (self.x_to / 100) * self.hover_prob,
                self.hover_row * self.tv.txt_height + yp,
            )
            cr.stroke()

    def on_key_press(self, widget, event):
        if cfg.key["hold_editor"].matches(event):
            if not self.clearing:
                if not self.lock:
                    self.lock = True
                    if not self.confirmed:
                        self.locked = self.tv.trk[self.col][self.row].prob

        if 65505 <= event.keyval <= 65506:  # shift
            if self.hover_row > -1 and self.confirmed:
                self.line = self.hover_row

    def on_key_release(self, widget, event):
        if self.line > -1:
            self.line = -1
            self.tv.redraw()

        if self.clearing:
            return False

        if not self.confirmed:
            self.lock = False
            self.locked = self.tv.trk[self.col][self.row].prob

        if self.confirmed:
            self.lock = False

        return False

    def on_motion(self, widget, event):
        # edit single probbie in place
        if (
            not self.clearing
            and not self.confirmed
            and not self.lock
            and self.line == -1
        ):
            if event.x < self.x_from:
                prob = self.start_value - (
                    (event.y - self.event_y) / cfg.drag_edit_divisor
                )
                prob = max(min(prob, 100), 0)

                self.locked = prob

                self.tv.trk[self.col][self.row].prob = prob
                self.tv.redraw(self.row)
                return True

        if not self.confirmed:
            if event.x >= self.x_from and event.x <= self.x_from + self.x_to:
                self.confirmed = True

            if not self.confirmed and not self.clearing:
                return False

        new_hover_row = max(
            0, min(int(event.y / self.tv.txt_height), self.tv.trk.nrows - 1)
        )
        self.hover_row = new_hover_row

        if self.tv.trk[self.col][self.row].type not in (1, 2):
            return False

        y1 = new_hover_row * self.tv.txt_height
        y2 = y1 + self.tv.txt_height

        prob = 0

        if (
            (event.y > y1 and event.y < y2)
            or (event.y > y1 and new_hover_row >= self.tv.trk.nrows - 1)
            or new_hover_row == 0
        ):
            prob = min(max(((event.x - self.x_from) / self.x_to) * 100, 0), 100)

        if self.line > -1:
            rs = self.line
            re = min(self.trk.nrows - 1, int(event.y / self.tv.txt_height))
            vs = self.tv.trk[self.col][self.line].prob
            self.hover_prob = prob

            if abs(re - rs) > 0:
                d = (prob - vs) / (re - rs)
                vv = vs

                if re > rs:
                    rs += 1
                    vv += d
                    re += 1
                else:
                    rs, re = re, rs
                    prob, vs = vs, prob

                    d = (prob - vs) / (re - rs)
                    vv = vs

                for r in range(rs, re):
                    if r > -1 and r <= self.tv.trk.nrows:
                        if self.tv.trk[self.col][r].type == 1:
                            self.tv.trk[self.col][r].prob = vv
                    vv += d

            self.tv.redraw()
            return

        if self.lock:
            prob = self.locked

        if self.clearing:
            prob = 0

        if new_hover_row > -1:
            if not self.lock and self.tv.trk[self.col][new_hover_row].type == 1:
                self.locked = prob

            self.tv.trk[self.col][new_hover_row].prob = prob
            self.tv.redraw(new_hover_row, new_hover_row)
        return True
