# timelineview.py - Valhalla Tracker
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

import math
from vht import cfg, mod
import cairo
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk


class TimelineView(Gtk.DrawingArea):
    def __init__(self):
        super(TimelineView, self).__init__()

        self.set_events(
            Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.SCROLL_MASK
            | Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
        )

        self._surface = None
        self._context = None

        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.on_button_release)
        self.connect("motion-notify-event", self.on_motion)
        self.connect("draw", self.on_draw)
        self.connect("configure-event", self.on_configure)
        self.connect("scroll-event", self.on_scroll)
        self.connect("leave-notify-event", self.on_leave)

    def on_configure(self, wdg, event):
        self.configure()
        self.redraw()
        return True

    def on_button_press(self, widget, event):
        return True

    def on_button_release(self, widget, event):
        return True

    def on_motion(self, widget, event):
        return True

    def on_leave(self, wdg, prm):
        return True

    def zoom(self, i):
        cfg.mixer_font_size += i
        cfg.mixer_font_size = min(max(1, cfg.mixer_font_size), 230)
        self.configure()
        self.redraw()

        if self._menu_handle > -1:
            self.pop_point_to(self._menu_handle)

    def zoom(self, i):
        cfg.mixer_font_size += i
        cfg.mixer_font_size = min(max(1, cfg.mixer_font_size), 230)
        self.configure()
        self.redraw()

    def on_scroll(self, widget, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            if event.direction == Gdk.ScrollDirection.UP:
                self.zoom(1)
            if event.direction == Gdk.ScrollDirection.DOWN:
                self.zoom(-1)
            return True
        return False

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

    def redraw(self, col=-1):
        cr = self._context

        if not cr:
            return

        w = self.get_allocated_width()
        h = self.get_allocated_height()
        *_, dx, _ = cr.text_extents("dupa")

        redr = []

    def on_draw(self, widget, cr):
        cr.set_source_surface(self._surface, 0, 0)
        cr.paint()

        return True

    def tick(self):
        self.redraw()
        return True
