# sidetrackview.py - Valhalla Tracker
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

from vht.trackviewpointer import TrackviewPointer
from vht import mod, cfg
import math
import cairo

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk


class SideTrackView(Gtk.DrawingArea):
    def __init__(self, seq, parent):
        super(SideTrackView, self).__init__()

        self.seq = seq
        self.trk = None
        self.parent = parent
        self.edit = None

        self._pointer = TrackviewPointer(self, self.trk, self.seq)

        self.set_events(
            Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
            | Gdk.EventMask.ENTER_NOTIFY_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
            | Gdk.EventMask.KEY_RELEASE_MASK
        )

        self.connect("draw", self.on_draw)
        self.connect("configure-event", self.on_configure)
        self.connect("motion-notify-event", self.on_motion)
        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.on_button_release)
        self.connect("leave-notify-event", self.on_leave)
        self.connect("destroy", self.on_destroy)

        self._surface = None
        self._context = None
        self._back_surface = None
        self._back_context = None

        self.zero_pattern_surface = None
        self.zero_pattern_highlight = -1
        self.zero_pattern = None

        self.hover = None

    def __del__(self):
        if self._surface:
            self._surface.finish()

        if self._back_surface:
            self._surface.finish()

    def on_button_press(self, widget, event):
        print("butt press", event)
        return True

    def on_button_release(self, widget, event):
        print("butt release", event)
        return True

    def configure(self):
        self._back_context.select_font_face(
            cfg.seq_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD
        )

        self._back_context.set_font_size(self.parent.font_size)

        w = self.get_allocated_width()
        h = self.get_allocated_height()

        cr = self._back_context
        crf = self._context
        crf.set_source_surface(self._back_surface)

        (x, y, width, height, dx, dy) = cr.text_extents("000|")

        self.txt_height = float(height) * self.spacing * cfg.seq_spacing
        self.txt_width = int(dx)

        nw = dx
        nh = self.txt_height * self.seq.length + 10
        self.set_size_request(nw, nh)
        self.width = nw

        recr_cr = False

        if not self.zero_pattern_surface:
            recr_cr = True
        else:
            if self.zero_pattern_surface.get_width() != nw:
                recr_cr = True

            if self.zero_pattern_surface.get_height() != round(self.txt_height * 2):
                recr_cr = True

        if self.zero_pattern_highlight != self.parent.highlight:
            self.zero_pattern_highlight = self.parent.highlight
            recr_cr = True

        if recr_cr:
            # zero pattern
            if self.zero_pattern_surface:
                self.zero_pattern_surface.finish()

            self.zero_pattern_surface = self._back_surface.create_similar(
                cairo.CONTENT_COLOR_ALPHA, round(self.width), round(self.txt_height * 2)
            )

            cr = cairo.Context(self.zero_pattern_surface)

            cr.set_source_rgb(*(col * cfg.intensity_background for col in cfg.colour))
            cr.rectangle(0, 0, self.width, self.txt_height)
            cr.fill()
            cr.set_source_rgb(
                *(
                    col * cfg.intensity_background * cfg.even_highlight
                    for col in cfg.colour
                )
            )
            cr.rectangle(0, self.txt_height, self.width, self.txt_height)
            cr.fill()

            self.zero_pattern = cairo.SurfacePattern(self.zero_pattern_surface)
            self.zero_pattern.set_extend(cairo.Extend.REPEAT)
            matrix = cairo.Matrix()
            # because rowheight is float
            matrix.scale(1.0, round(self.txt_height * 2) / (self.txt_height * 2))
            self.zero_pattern.set_matrix(matrix)

    def redraw(self, from_row=-666, to_row=-666, ctrl=None):
        cr = self._back_context
        crf = self._context
        crf.set_source_surface(self._back_surface)

        w = self.get_allocated_width()
        h = self.get_allocated_height()

        wnd = self.get_window()
        ir = Gdk.Rectangle()

        complete = False
        if from_row == -666 and to_row == -666:
            complete = True

        if from_row != -666 and to_row == -666:
            to_row = from_row

        if from_row > to_row:
            from_row, to_row = to_row, from_row

        (x, y, width, height, dx, dy) = cr.text_extents("000|")

        self.txt_height = float(height) * self.spacing * cfg.seq_spacing
        self.txt_width = int(dx)

        nw = dx
        nh = self.txt_height * self.seq.length + 10
        self.set_size_request(nw, nh)
        self.width = nw
        if complete:
            cr.set_source_rgb(*(col * cfg.intensity_background for col in cfg.colour))
            cr.rectangle(0, 0, w, h)
            cr.fill()

        rows_to_draw = []

        (x, y, width, height, dx, dy) = cr.text_extents(cfg.row_number_format % 999)

        if complete:
            self.configure()
            rows_to_draw = range(self.seq.length)
        else:
            for r in range(self.seq.length):
                if from_row <= r <= to_row:
                    rows_to_draw.append(r)

        for r in rows_to_draw:
            even_high = cfg.even_highlight
            if r % 2 == 0:
                even_high = 1.0

            cr.set_source_rgb(
                *(col * cfg.intensity_background * (even_high) for col in cfg.colour)
            )
            cr.rectangle(0, r * self.txt_height, w, self.txt_height)
            cr.fill()

            if self.hover and r == self.hover[1]:
                cr.set_source_rgb(
                    *(col * cfg.intensity_txt_highlight * 1.2 for col in cfg.colour)
                )
            else:
                if r % self.seq.rpb == 0:
                    cr.set_source_rgb(
                        *(col * cfg.intensity_txt_highlight for col in cfg.colour)
                    )
                else:
                    cr.set_source_rgb(*(col * cfg.intensity_txt for col in cfg.colour))

            yy = (r + 1) * self.txt_height - ((self.txt_height - height) / 2.0)
            cr.move_to(x, yy)
            cr.show_text(cfg.row_number_format % r)

            if not complete:
                (x, y, width, height, dx, dy) = cr.text_extents("|")
                cr.set_source_rgb(*(col * cfg.intensity_lines for col in cfg.colour))
                cr.set_antialias(cairo.ANTIALIAS_NONE)
                cr.set_line_width((self.parent.font_size / 6.0) * cfg.seq_line_width)
                cr.move_to(self.txt_width - (dx / 2), 0)
                cr.line_to(
                    self.txt_width - (dx / 2), (self.seq.length) * self.txt_height
                )
                cr.stroke()

                ir.x = 0
                ir.width = w
                ir.y = int(r * self.txt_height)
                ir.height = self.txt_height * 2
                crf.rectangle(ir.x, ir.y, ir.width, ir.height)
                crf.fill()
                wnd.invalidate_rect(ir, False)

        if complete:
            (x, y, width, height, dx, dy) = cr.text_extents("|")
            cr.set_source_rgb(*(col * cfg.intensity_lines for col in cfg.colour))
            cr.set_antialias(cairo.ANTIALIAS_NONE)
            cr.set_line_width((self.parent.font_size / 6.0) * cfg.seq_line_width)
            cr.move_to(self.txt_width - (dx / 2), 0)
            cr.line_to(self.txt_width - (dx / 2), (self.seq.length) * self.txt_height)
            cr.stroke()

            crf.set_source_surface(self._back_surface)
            crf.paint()
            self.queue_draw()

        return

    def reblit(self, from_row=-666, to_row=-666):
        crf = self._context
        crf.set_source_surface(self._back_surface)

        w = self.get_allocated_width()

        wnd = self.get_window()
        ir = Gdk.Rectangle()

        complete = False
        if from_row == -666 and to_row == -666:
            complete = True

        if from_row != -666 and to_row == -666:
            to_row = from_row

        if from_row > to_row:
            from_row, to_row = to_row, from_row

        # side_column
        rows_to_draw = []

        if complete:
            rows_to_draw = range(self.seq.length)
        else:
            for r in range(self.seq.length):
                if from_row <= r <= to_row:
                    rows_to_draw.append(r)

        if not complete:
            for r in rows_to_draw:
                ir.x = 0
                ir.width = w
                ir.y = int(r * self.txt_height)
                ir.height = self.txt_height * 2
                crf.rectangle(ir.x, ir.y, ir.width, ir.height)
                crf.fill()
                wnd.invalidate_rect(ir, False)

        if complete:
            crf.set_source_surface(self._back_surface)
            crf.paint()
            self.queue_draw()

        return

    def redraw_full(self):
        # may be called before realising
        if not self._back_context:
            return

        self.configure()
        self.redraw()
        self.queue_draw()

    def on_configure(self, wdg, event):
        if self._surface:
            self._surface.finish()

        if self._back_surface:
            self._back_surface.finish()

        self._surface = wdg.get_window().create_similar_surface(
            cairo.CONTENT_COLOR, wdg.get_allocated_width(), wdg.get_allocated_height()
        )

        self._back_surface = wdg.get_window().create_similar_surface(
            cairo.CONTENT_COLOR, wdg.get_allocated_width(), wdg.get_allocated_height()
        )

        self._context = cairo.Context(self._surface)
        self._context.set_antialias(cairo.ANTIALIAS_NONE)

        self._back_context = cairo.Context(self._back_surface)
        self._back_context.set_antialias(cairo.ANTIALIAS_NONE)

        self.configure()

        self.redraw()
        self.tick()
        return True

    def on_motion(self, widget, event):
        return True

    def on_leave(self, wdg, prm):
        self.hover = None

    def on_destroy(self, wdg):
        if self._surface:
            self._surface.finish()

        if self._back_surface:
            self._back_surface.finish()

        if self.zero_pattern_surface:
            self.zero_pattern_surface.finish()

    def tick(self):
        if self._context and self._back_context:
            self._pointer.draw(self.seq.pos)

        return True

    def on_draw(self, widget, cr):
        cr.set_source_surface(self._surface, 0, 0)
        cr.paint()
        return False
