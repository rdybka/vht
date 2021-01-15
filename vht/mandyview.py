# mandyview.py - Valhalla Tracker
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
import cairo
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

from vht import cfg, mod


class MandyView(Gtk.DrawingArea):
    def __init__(self, trk, parent, vector=True):
        super(MandyView, self).__init__()

        self.set_can_focus(True)
        self.parent = parent
        self.trk = trk

        self.mandy = trk.mandy
        # self.mandy.active = 1
        self.entered = False
        self.show_info = False
        self.show_crosshair = True

        self.set_events(
            Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.SCROLL_MASK
            | Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.ENTER_NOTIFY_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
            | Gdk.EventMask.KEY_RELEASE_MASK
        )

        self.connect("draw", self.on_draw)
        self.connect("configure-event", self.on_configure)
        self.connect("scroll-event", self.on_scroll)
        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.on_button_release)
        self.connect("enter-notify-event", self.on_enter)
        self.connect("motion-notify-event", self.on_motion)
        self.connect("key-press-event", self.on_key_press)
        self.connect("key-release-event", self.on_key_release)

        self._surface = None
        self._context = None
        self.vector = vector

        self.translate_start = None

    def on_configure(self, wdg, event):
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
        self._context.select_font_face(
            cfg.console_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD
        )
        self._context.set_font_size(10)

        (q, w, e, self._txt_height, r, t) = self._context.text_extents("|")
        (y, u, i, o, self._txt_width, p) = self._context.text_extents("0")

        self.mandy.set_rgb(*[c * 255 for c in cfg.mandy_colour])

        self.redraw()

    def redraw(self):
        cr = self._context

        if not cr:
            return

        w = self.get_allocated_width()
        h = self.get_allocated_height()

        if self.vector:
            cr.set_source_rgb(*(col * cfg.intensity_background for col in cfg.colour))
            cr.rectangle(0, 0, w, h)
            cr.fill()
        else:
            cr.set_source(self.gen_pix(w, h))
            cr.rectangle(0, 0, w, h)
            cr.fill()

        pts = self.mandy.render(w, h)

        if self.show_crosshair:
            cr.set_source_rgb(*(cfg.mandy_crosshair_colour))
            cx = w / 2
            cy = h / 2

            cr.set_line_width(1)
            cr.arc(cx, cy, 1, 0, math.pi * 2)
            cr.stroke()

            sz = 10
            r = self.mandy.rot
            cs = math.cos(-r + math.pi / 2)
            sn = math.sin(-r + math.pi / 2)
            cr.move_to(cx + sz / 2 * cs, cy - sz / 2 * sn)
            cr.line_to(cx + sz * cs, cy - sz * sn)
            cr.stroke()

        info = self.mandy.info if self.show_info else None
        if info:
            yy = 0
            for inf in info.split("\n"):
                *_, txtdy, txtdx, _ = cr.text_extents(inf)
                cr.set_source_rgb(*(cfg.star_colour))
                cr.move_to(0, txtdy + yy)
                yy += txtdy
                cr.show_text(inf)

        self.get_window().invalidate_rect(None, False)

    def gen_pix(self, w, h, d=1):
        w = int(w // d)
        h = int(h // d)
        fmt = cairo.Format.RGB24
        stride = fmt.stride_for_width(w)

        srf = cairo.SurfacePattern(
            cairo.ImageSurface.create_for_data(
                self.mandy.get_pixels(w, h, stride), fmt, w, h
            )
        )

        srf.set_filter(cairo.Filter.FAST)
        matrix = cairo.Matrix(xx=1 / d, yy=1 / d)
        srf.set_matrix(matrix)
        return srf

    def on_scroll(self, widget, event):
        ctrl_hold = False
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            ctrl_hold = True

        if ctrl_hold:
            if event.direction == Gdk.ScrollDirection.UP:
                self.mandy.miter += 1
            if event.direction == Gdk.ScrollDirection.DOWN:
                self.mandy.miter -= 1

        # just scroll - zoom
        if not ctrl_hold:
            if event.direction == Gdk.ScrollDirection.UP:
                self.mandy.zoom /= 1.05
            if event.direction == Gdk.ScrollDirection.DOWN:
                self.mandy.zoom *= 1.05

    def on_draw(self, widget, cr):
        if not self._surface:
            return False

        cr.set_source_surface(self._surface, 0, 0)
        cr.paint()
        return True

    def on_motion(self, widget, event):
        w = self.get_allocated_width()
        h = self.get_allocated_height()

        if self.translate_start:
            x = event.x - self.translate_start[0]
            y = event.y - self.translate_start[1]

            handled = False
            if event.state & Gdk.ModifierType.CONTROL_MASK:
                self.mandy.screen_zoom(x, y, w, h)
                handled = True

            if event.state & Gdk.ModifierType.SHIFT_MASK:
                handled = True
                self.mandy.screen_rotate(x, y, w, h)

            if not handled:
                self.mandy.screen_translate(x, y, w, h)

            self.translate_start = (event.x, event.y)
            return

        self.mandy.set_cxy(event.x, event.y)

    def on_button_press(self, widget, event):
        # filter double clicks
        if (
            event.type == Gdk.EventType._2BUTTON_PRESS
            or event.type == Gdk.EventType._3BUTTON_PRESS
        ):
            return

        if event.button == 2:
            self.translate_start = [event.x, event.y]

    def on_button_release(self, widget, event):
        self.translate_start = None

    def on_key_press(self, widget, event):
        if cfg.key["mandy_show_info"].matches(event):
            self.show_info = not self.show_info
            return True

        if cfg.key["mandy_show_crosshair"].matches(event):
            self.show_crosshair = not self.show_crosshair
            return True

        if cfg.key["mandy_reset_rotation"].matches(event):
            self.mandy.rot = 0
            return True

        if cfg.key["mandy_reset_translation"].matches(event):
            self.mandy.set_xy(-0.7, 0)
            return True

        if cfg.key["mandy_reset_zoom"].matches(event):
            self.mandy.zoom = 6
            return True

        if cfg.key["mandy_reset"].matches(event):
            self.mandy.zoom = 6
            self.mandy.rot = 0
            self.mandy.set_xy(-0.7, 0)
            return True

        if cfg.key["mandy_pause"].matches(event):
            self.mandy.pause = not self.mandy.pause
            return True

        return False

    def on_key_release(self, widget, event):
        return False

    def tick(self, wdg, param):
        self.redraw()
        return True

    def on_enter(self, wdg, prm):
        self.entered = True
        self.grab_focus()
