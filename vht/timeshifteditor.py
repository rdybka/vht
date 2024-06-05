# timeshifteditor.py - vahatraker
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


class TimeshiftEditor:
    def __init__(self, tv, col, row, event):
        self.col = col
        self.row = row
        self.tv = tv
        self.event_y = event.y

        self.trk = tv.trk

        self.confirmed = False
        self.clearing = False
        self.lock = False
        self.locked = self.trk[col][row].delay

        if event.type == Gdk.EventType.BUTTON_PRESS:
            self.range_mode = True if event.button == 2 else False
        else:
            self.range_mode = False

        if self.range_mode:
            self.locked = self.trk[col][row].delay_range

        self.start_value = self.locked

        self.x_from = 0
        self.x_to = 0
        self.width = 127

    def precalc(self, cr):
        (x, y, width, height, dx, dy) = cr.text_extents("0")
        self.width = max((cfg.timeshift_editor_char_width * width), 99)
        self.x_from = self.tv.txt_width * self.col + self.tv.fld_width * 3 - dx / 2
        self.x_to = self.width

        if self.col == len(self.trk) - 1:
            self.width += dx / 2

    def draw(self, cr, col, r, rw):
        yh = cfg.editor_row_height * self.tv.txt_height
        yp = (self.tv.txt_height - yh) / 2.0

        cr.set_line_width(1.0)
        cr.set_source_rgba(*(col * cfg.intensity_txt for col in cfg.colour), 1)
        cr.rectangle(
            self.x_from + (self.x_to / 2),
            r * self.tv.txt_height + yp,
            (self.x_to / 100) * rw.delay,
            yh,
        )
        cr.fill()

        midp = self.x_from + (self.x_to / 2)
        cr.set_source_rgba(*(col * cfg.intensity_txt for col in cfg.colour), 1.0)
        cr.rectangle(self.x_from, r * self.tv.txt_height + yp, self.x_to, yh)
        cr.move_to(midp, r * self.tv.txt_height + (yp * 0.5))
        cr.line_to(midp, (r + 1) * self.tv.txt_height - (yp * 0.5))
        cr.stroke()

        if rw.delay_range:
            cr.set_line_width(3.0)
            cr.set_source_rgba(
                *(col * cfg.intensity_txt_highlight for col in cfg.colour), 1
            )

            onep = self.x_to / 100

            x1 = max(
                midp + onep * rw.delay - (self.x_to / 100.0) * rw.delay_range,
                self.x_from,
            )
            x2 = min(
                midp + onep * rw.delay + (self.x_to / 100.0) * rw.delay_range,
                self.x_to + self.x_from,
            )

            cr.move_to(x1, r * self.tv.txt_height + yp)
            cr.line_to(x2, r * self.tv.txt_height + yp)
            cr.stroke()

    def on_key_press(self, widget, event):
        if cfg.key["hold_editor"].matches(event):
            if not self.clearing:
                if not self.lock:
                    self.lock = True
                    if not self.confirmed:
                        self.locked = self.tv.trk[self.col][self.row].delay

    def on_key_release(self, widget, event):
        if self.clearing:
            return False

        if not self.confirmed:
            self.lock = False
            self.locked = self.tv.trk[self.col][self.row].delay

        if self.confirmed:
            self.lock = False

        return False

    def on_motion(self, widget, event):
        # edit single in place
        if not self.clearing and not self.confirmed and not self.lock:
            if event.x < self.x_from and not self.range_mode:
                vel = self.trk[self.col][self.row].delay

                vel = self.start_value + (
                    (event.y - self.event_y) / cfg.drag_edit_divisor
                )
                vel = max(min(vel, 49), -49)

                self.locked = vel

                self.tv.trk[self.col][self.row].delay = vel
                self.tv.redraw(self.row)
                return True
            elif self.range_mode:
                rng = max(
                    min(
                        self.start_value
                        + ((event.y - self.event_y) / cfg.drag_edit_divisor),
                        49,
                    ),
                    0,
                )

                self.locked = rng

                self.tv.trk[self.col][self.row].delay_range = rng
                self.tv.redraw(self.row)
                return True

        if not self.confirmed:
            if event.x >= self.x_from and event.x <= self.x_from + self.x_to:
                self.confirmed = True

            if not self.confirmed and not self.clearing:
                return False

        new_hover_row = min(int(event.y / self.tv.txt_height), self.tv.trk.nrows - 1)

        if not 0 < self.tv.trk[self.col][self.row].type < 3:
            return False

        y1 = new_hover_row * self.tv.txt_height
        y2 = y1 + self.tv.txt_height

        vel = 0

        if (
            (event.y > y1 and event.y < y2)
            or (event.y > y1 and new_hover_row >= self.tv.trk.nrows - 1)
            or (new_hover_row == 0)
        ):
            vel = min(max(((event.x - self.x_from) / self.x_to) * 98.0, 0), 98)
            vel = vel - 49

        if new_hover_row > -1:
            if self.lock:
                vel = self.locked

            if self.clearing:
                vel = 0
                self.tv.trk[self.col][new_hover_row].delay_range = 0

            if not self.lock and self.tv.trk[self.col][new_hover_row].type == 1:
                self.locked = vel

            self.tv.trk[self.col][new_hover_row].delay = vel
            self.tv.redraw(new_hover_row, new_hover_row)
        return True
