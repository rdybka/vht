# sequencelistview.py - Valhalla Tracker
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

import math
from vht import cfg, mod
import cairo
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk

from vht.sequencelistviewpopover import *


class SequenceListView(Gtk.DrawingArea):
    def __init__(self):
        super(SequenceListView, self).__init__()

        self.set_events(
            Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.SCROLL_MASK
            | Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
        )

        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.on_button_release)
        self.connect("motion-notify-event", self.on_motion)
        self.connect("draw", self.on_draw)
        self.connect("configure-event", self.on_configure)
        self.connect("scroll-event", self.on_scroll)
        self.connect("leave-notify-event", self.on_leave)

        self._surface = None
        self._context = None

        self._drag = False
        self._move_handle = -1
        self._highlight = -1
        self._menu_handle = -1
        self._popup = SequenceListViewPopover(self)

    def configure(self):
        win = self.get_window()
        if not win:
            return

        if self._surface:
            self._surface.finish()

        self._surface = self.get_window().create_similar_surface(
            cairo.CONTENT_COLOR, self.get_allocated_width(), self.get_allocated_height()
        )

        self._context = cairo.Context(self._surface)
        self._context.set_antialias(cairo.ANTIALIAS_DEFAULT)
        self._context.set_line_width((cfg.mixer_font_size / 6.0) * cfg.seq_line_width)
        self._context.select_font_face(
            cfg.mixer_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD
        )
        self._context.set_font_size(cfg.mixer_font_size)

        (q, w, e, self._txt_height, r, t) = self._context.text_extents("|")
        (y, u, i, o, self._txt_width, p) = self._context.text_extents("0")
        self._shining_stars = [False] * len(mod)
        self._twinkling_lines = [(0, 1)] * len(mod)
        self._highlight = -1

        req_w = (self._txt_height * cfg.mixer_padding) * len(mod)
        w = self.get_allocated_width()

        self.set_size_request(req_w, 2)

    def on_configure(self, wdg, event):
        self.configure()
        self.redraw()
        return True

    def swap_seq(self, s0, s1):
        mod.swap_sequence(s0, s1)
        mod.extras[s0], mod.extras[s1] = mod.extras[s1], mod.extras[s0]

        old = s0
        self._move_handle = s1
        self._highlight = s1
        if old == mod.curr_seq:
            mod.curr_seq = self._move_handle
            mod.mainwin._sequence_view.prop_view.redraw()
        else:
            if self._move_handle == mod.curr_seq:
                mod.curr_seq = old
                mod.mainwin._sequence_view.prop_view.redraw()

        self.redraw(old)
        self.redraw(s1)

    def on_motion(self, widget, event):
        curr = int(event.x / (self._txt_height * cfg.mixer_padding))
        oldh = self._highlight

        # if self._popup.pooped:
        #    return

        if self._drag:
            curr = max(min(curr, len(mod) - 1), 0)
            if self._move_handle != curr:
                delta = 1
                if curr < self._move_handle:
                    delta *= -1

                for s in range(self._move_handle, curr, delta):
                    self.swap_seq(s, s + delta)

            return True

        if curr < len(mod):
            if event.y > self.get_allocated_height() - self._txt_height * 2:
                self._move_handle = curr
            else:
                self._move_handle = -1

            self._highlight = curr
            self.redraw(self._highlight)

            if event.y < self._txt_height:
                self._menu_handle = curr

                if self._popup.pooped:
                    self.pop_point_to(curr)
                    self._popup.refresh()
                    self.redraw()
            else:
                if self._menu_handle > -1:
                    old = self._menu_handle
                    self._menu_handle = -1
                    self.redraw(old)
        else:
            self._highlight = -1
            self._move_handle = -1
            self._menu_handle = -1

        if -1 < oldh < len(mod) and oldh != self._highlight:
            self.redraw(oldh)

    def on_button_press(self, widget, event):
        if event.button != cfg.select_button:
            return False

        # if self._popup.pooped:
        #    return True

        old = mod.curr_seq

        curr = int(event.x / (self._txt_height * cfg.mixer_padding))
        if curr == self._move_handle:
            self._drag = True
            return True

        if curr < len(mod):
            if not "mouse_cfg" in mod.extras[curr][-1]:
                mod.extras[curr][-1]["mouse_cfg"] = [3, 2, 0]

            if event.y < self._txt_height:
                self.pop_point_to(curr)
                self._popup.pop(curr)
            else:
                mod.curr_seq = curr
                self.redraw(curr)

        if old > -1:
            self.redraw(old)

        if old != mod.curr_seq:
            mod.mainwin._sequence_view.switch(mod.curr_seq)

        return True

    def on_button_release(self, widget, event):
        if event.button != cfg.select_button:
            return False

        self._drag = False

        return True

    def on_leave(self, wdg, prm):
        self._highlight = -1
        self._menu_handle = -1
        self.redraw()

    def pop_point_to(self, r):
        rect = Gdk.Rectangle()
        x = (self._txt_height * cfg.mixer_padding) * r
        x += ((self._txt_height * cfg.mixer_padding) - self._txt_height) / 2.0
        rect.x = x
        rect.width = self._txt_width
        rect.height = self._txt_height
        self._popup.set_pointing_to(rect)
        self._popup.curr = r

    def zoom(self, i):
        cfg.mixer_font_size += i
        cfg.mixer_font_size = min(max(1, cfg.mixer_font_size), 230)
        self.configure()
        self.redraw()

        if self._menu_handle > -1:
            self.pop_point_to(self._menu_handle)

    def on_scroll(self, widget, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            if event.direction == Gdk.ScrollDirection.UP:
                self.zoom(1)
            if event.direction == Gdk.ScrollDirection.DOWN:
                self.zoom(-1)
            return True
        return False

    def redraw(self, col=-1):
        cr = self._context

        w = self.get_allocated_width()
        h = self.get_allocated_height()

        redr = []
        if col == -1:
            redr = list(range(len(mod)))
            cr.set_source_rgb(*(col * cfg.intensity_background for col in cfg.colour))
            cr.rectangle(0, 0, w, h)
            cr.fill()
        else:
            redr.append(col)

        for r in redr:
            x = (self._txt_height * cfg.mixer_padding) * r
            x += ((self._txt_height * cfg.mixer_padding) - self._txt_height) / 2.0

            gradient = cairo.LinearGradient(0, 0, 0, h)
            gradient.add_color_stop_rgb(
                0.0, *(col * cfg.intensity_background for col in cfg.mixer_colour)
            )
            gradient.add_color_stop_rgb(
                0.05, *(col * cfg.intensity_txt for col in cfg.mixer_colour)
            )

            if r == self._highlight:
                gradient.add_color_stop_rgb(
                    1.0, *(col * cfg.intensity_txt for col in cfg.mixer_colour)
                )
            else:
                gradient.add_color_stop_rgb(
                    1.0, *(col * cfg.intensity_background for col in cfg.mixer_colour)
                )

            cr.set_source_rgb(*(col * cfg.intensity_background for col in cfg.colour))
            cr.rectangle(x - self._txt_height / 3, 0, self._txt_height * 1.23, h)
            cr.fill()

            cr.save()
            cr.set_source(gradient)
            cr.rectangle(x - self._txt_height / 3, 0, self._txt_height * 1.23, h)
            cr.fill()
            cr.restore()

            if self._popup.pooped and self._popup.curr == r:
                cr.set_source_rgb(
                    *(col * cfg.intensity_txt_highlight for col in cfg.star_colour)
                )
            elif self._menu_handle == r and not self._popup.pooped:
                cr.set_source_rgb(
                    *(col * cfg.intensity_txt_highlight for col in cfg.star_colour)
                )
            else:
                cr.set_source_rgb(0, 0, 0)

            cr.move_to(x, self._txt_height)
            cr.show_text("*")

            cr.set_source_rgb(0, 0, 0)
            if r == mod.curr_seq:
                cr.set_source_rgb(
                    *(col * cfg.intensity_txt_highlight for col in cfg.mixer_colour)
                )

            cr.save()
            cr.rectangle(0, 0, w, h - self._txt_height * 2)
            cr.clip()
            cr.move_to(x, self._txt_height)
            cr.rotate(math.pi / 2.0)

            txt = cfg.sequence_name_format % (len(mod) - 1)
            if "sequence_name" in mod.extras[r][-1]:
                cr.show_text(mod.extras[r][-1]["sequence_name"])
            else:
                for rr in mod.extras.values():
                    if "sequence_name" in rr[-1]:
                        if rr[-1]["sequence_name"] == txt:
                            txt = txt + "_"

                mod.extras[r][-1]["sequence_name"] = txt
                cr.show_text(txt)

            cr.restore()

            if r == self._move_handle and r == self._highlight:
                cr.set_source_rgb(
                    *(col * cfg.intensity_txt_highlight for col in cfg.colour)
                )
            else:
                cr.set_source_rgb(
                    *(col * cfg.intensity_background for col in cfg.colour)
                )

            cr.move_to(x, h - self._txt_height)
            cr.show_text("=")

            cr.set_source_rgb(*(col * cfg.intensity_lines for col in cfg.mixer_colour))
            cr.set_line_width((cfg.mixer_font_size / 10.0) * cfg.seq_line_width)
            cr.move_to(x + self._txt_height, self._txt_height / 4.0)
            cr.line_to(x + self._txt_height, h)
            cr.stroke()

        self.queue_draw()

    def on_draw(self, widget, cr):
        cr.set_source_surface(self._surface, 0, 0)
        cr.paint()
        return False

    def tick(self):
        # if self.trgview.play_mode_cb.props.popup_shown:
        #    self.time_want_to_leave = 0
        #    return True

        return True
