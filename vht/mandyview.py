# mandyview.py - vahatraker
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

import math
import cairo
import gi
import os
import random
import time

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf

from vht import cfg, mod


class MandyView(Gtk.DrawingArea):
    def __init__(self, trk, parent, vector=True):
        super(MandyView, self).__init__()

        self.set_can_focus(True)
        self.parent = parent
        self.trk = trk

        self.mandy = trk.mandy

        self.entered = False
        self.show_info = False
        self.show_crosshair = True

        self.turtle_img = cairo.ImageSurface.create_from_png(
            mod.data_path + os.sep + "mandy.png"
        )
        self.turtle_gfx = cairo.SurfacePattern(self.turtle_img)
        self.turtle_gfx.set_filter(cairo.Filter.NEAREST)

        self.bailed_txt = None

        self.blank_curs = Gdk.Cursor.new(Gdk.CursorType.BLANK_CURSOR)

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

        self.translate_start = None
        self.translate_julia = False

        self.last_xy = (0, 0)
        self.trc_pos = None

        self.last_t = time.time_ns()

        self.refollow = False

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
        self._context.set_antialias(cairo.ANTIALIAS_NONE)
        self._context.select_font_face(
            cfg.console_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD
        )
        self._context.set_font_size(8)

        (q, w, e, self._txt_height, r, t) = self._context.text_extents("|")
        (y, u, i, o, self._txt_width, p) = self._context.text_extents("0")

        self.mandy.set_rgb(*[c * 255 for c in cfg.mandy_colour])

        self.redraw()

    def redraw(self):
        self.mandy.set_rgb(*[c * 255 for c in cfg.mandy_colour])
        cr = self._context

        if not cr:
            return

        w = self.get_allocated_width()
        h = self.get_allocated_height()

        cr.set_source(self.gen_pix(w, h))
        cr.rectangle(0, 0, w, h)
        cr.fill()

        npts = self.mandy.render(w, h)
        if npts:
            tp = 0
            pts = self.mandy.get_points()
            pt = 0
            while pt < npts:
                p = pts[pt]
                if int(p) == 0:  # type change
                    pt += 1
                    tp = int(pts[pt])
                elif int(p) == 1:  # vect start
                    pt += 1
                    x = pts[pt]
                    pt += 1
                    y = pts[pt]
                    cr.move_to(x, y)
                elif int(p) == 2:  # vect point
                    pt += 1
                    x = pts[pt]
                    pt += 1
                    y = pts[pt]
                    cr.line_to(x, y)
                elif int(p) == 3:  # vect end
                    if tp == 0:
                        cr.stroke()
                    elif tp == 1:
                        cr.fill()
                elif int(p) == 4:  # vect col
                    pt += 1
                    col = pts[pt]
                    if col == 0:
                        cr.set_source_rgb(*(cfg.mandy_crosshair_colour))
                        cr.set_line_width(2)
                    if col == 1:
                        cr.set_source_rgb(*(cfg.star_colour))
                        cr.set_line_width(1)

                pt += 1

        fol = self.mandy.follow
        if self.show_crosshair and fol == -1:
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

        init_trc = self.mandy.init_tracy
        if init_trc:
            d = init_trc.disp
            cr.set_source_rgb(*(cfg.record_colour))
            cr.set_line_width(1)
            cr.arc(d["x"], d["y"], 5, 0, math.pi * 2)
            cr.fill()

        trtl_img_width = self.turtle_img.get_width()
        trtl_img_height = self.turtle_img.get_height()

        if self.mandy.active:
            for trcid, trc in enumerate(self.mandy):
                d = trc.disp

                if trcid == 0 and not self.trc_pos:
                    self.trc_pos = (d["x"], d["y"])

                tail = trc.tail
                tl = len(tail)

                tw = max(8, 8 * 0.5 / d["zoom"])
                sm = 2

                np = (
                    self.trc_pos[0] + (d["x"] - self.trc_pos[0]) / sm,
                    self.trc_pos[1] + (d["y"] - self.trc_pos[1]) / sm,
                )

                if math.isfinite(np[0]) and math.isfinite(np[1]):
                    self.trc_pos = np

                cr.move_to(np[0], np[1])
                for n, t in enumerate(tail):
                    cr.set_source_rgb(
                        *(col * (1 - (n / tl)) for col in cfg.star_colour)
                    )
                    cr.set_line_width(tw * (1 - (n / tl)))
                    cr.line_to(t[0] + 10 * math.cos(t[2]), t[1] + 10 * math.sin(t[2]))
                    cr.stroke()
                    cr.move_to(t[0], t[1])

                matrix = cairo.Matrix()
                matrix.translate(trtl_img_width / 2.0, trtl_img_height / 2.0)
                sc = d["zoom"] * 2
                sc = max(min(sc, 1), 0.01)

                # print(sc, np[0], np[1])
                matrix.scale(sc, sc)
                matrix.rotate(-d["r"])
                if trc.speed < 0:
                    matrix.rotate(math.pi)

                matrix.translate(-np[0], -np[1])
                self.turtle_gfx.set_matrix(matrix)

                cr.set_source(self.turtle_gfx)
                cr.rectangle(0, 0, w, h)
                cr.fill()

                if d["bailed"]:
                    ltr = "!!#?**%%?$@^<([funbikt41:"
                    txt = ""
                    ltxt = random.randint(3, 8)

                    while len(txt) < ltxt:
                        txt += ltr[random.randint(0, len(ltr) - 1)]

                    if not self.bailed_txt:
                        x = d["x"] + ((w / 8) * random.uniform(-1, 1))
                        y = d["y"] + ((h / 8) * random.uniform(-1, 1))
                        r = random.uniform(-math.pi / 2, math.pi / 2)
                        l = random.randint(2, 8)
                        s = random.randint(1, 3)
                        c = random.randint(1, 2)
                        self.bailed_txt = [txt, l, x, y, r, s, c]

                if self.bailed_txt:
                    self.bailed_txt[1] -= 1

                    *_, txtdy, txtdx, _ = cr.text_extents(self.bailed_txt[0])

                    x = d["x"] + ((w / 4) * random.uniform(-1, 1))
                    y = d["y"] + ((h / 4) * random.uniform(-1, 1))
                    cr.save()
                    cr.set_source_rgb(0, 0, 0)
                    cr.move_to(self.bailed_txt[2], self.bailed_txt[3])
                    cr.rotate(self.bailed_txt[4])
                    cr.scale(self.bailed_txt[5], self.bailed_txt[5])
                    cr.show_text(self.bailed_txt[0])
                    cr.restore()
                    cr.save()
                    if self.bailed_txt[6] == 1:
                        cr.set_source_rgb(*(cfg.record_colour))
                    else:
                        cr.set_source_rgb(*(cfg.star_colour))

                    cr.move_to(self.bailed_txt[2], self.bailed_txt[3])
                    cr.rotate(self.bailed_txt[4])
                    cr.scale(self.bailed_txt[5] * 1.1, self.bailed_txt[5] * 1.1)
                    cr.show_text(self.bailed_txt[0])
                    cr.restore()

                    if self.bailed_txt[1] == 0:
                        self.bailed_txt = None

        scan_trc = self.mandy.scan_tracy
        if (
            scan_trc
            and not self.translate_start
            and (self.mandy.follow == -1 or self.mandy.pause)
        ):
            d = scan_trc.disp
            cr.set_source_rgb(*(cfg.star_colour))
            cr.set_line_width(1)
            cr.arc(d["x"], d["y"], 5, 0, math.pi * 2)
            cr.fill()

        info = self.mandy.info if self.show_info else None
        if info:
            yy = 0
            for inf in info.split("\n"):
                *_, txtdy, txtdx, _ = cr.text_extents(inf)
                cr.set_source_rgb(*(cfg.star_colour))
                cr.move_to(0, txtdy + yy)
                yy += txtdy
                cr.show_text(inf)

        wnd = self.get_window()
        if wnd:
            wnd.invalidate_rect(None, False)

    def gen_pix(self, w, h, d=1):
        w = max(32, w)

        self.mandy.set_rgb(*[c * 255 for c in cfg.mandy_colour])
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
        shift_hold = False
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            ctrl_hold = True

        if event.state & Gdk.ModifierType.SHIFT_MASK:
            shift_hold = True

        if ctrl_hold:
            if event.direction == Gdk.ScrollDirection.UP:
                self.mandy.miter += 1
            if event.direction == Gdk.ScrollDirection.DOWN:
                self.mandy.miter -= 1

            self.parent.update()

        if shift_hold and len(self.mandy):
            if event.direction == Gdk.ScrollDirection.UP:
                self.mandy[0].speed += 1
            if event.direction == Gdk.ScrollDirection.DOWN:
                self.mandy[0].speed -= 1

            self.parent.update()

        # just scroll - zoom
        if not ctrl_hold and not shift_hold:
            if event.direction == Gdk.ScrollDirection.UP:
                self.mandy.zoom /= 1.05
            if event.direction == Gdk.ScrollDirection.DOWN:
                self.mandy.zoom *= 1.05

        return True

    def on_draw(self, widget, cr):
        if not self._surface:
            return False

        cr.set_source_surface(self._surface, 0, 0)
        cr.paint()
        return True

    def on_motion(self, widget, event):
        w = self.get_allocated_width()
        h = self.get_allocated_height()

        self.last_xy = (event.x, event.y)

        if self.translate_start:
            x = event.x - self.translate_start[0]
            y = event.y - self.translate_start[1]

            if self.mandy.follow == 0 and self.mandy.pause:
                self.mandy.follow = -1
                self.parent.update()

            handled = False
            if event.state & Gdk.ModifierType.CONTROL_MASK and not self.translate_julia:
                self.mandy.screen_zoom(x, y, w, h)
                handled = True

            if event.state & Gdk.ModifierType.SHIFT_MASK and not self.translate_julia:
                self.mandy.screen_rotate(x, y, w, h)
                handled = True

            if not handled:
                if self.translate_julia:
                    self.mandy.julia_translate(x, y, w, h)
                else:
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

        if event.button == cfg.select_button:
            scan_trc = self.mandy.scan_tracy
            if scan_trc:
                if self.mandy.follow == -1 or self.mandy.pause:
                    self.mandy.reinit_from_scan()
            else:
                self.translate_start = (event.x, event.y)
                self.translate_julia = False

        if event.button == cfg.delete_button:
            self.mandy.reset()

        if event.button == 2:
            self.translate_start = self.last_xy
            self.translate_julia = True

    def on_button_release(self, widget, event):
        self.mandy.set_cxy(event.x, event.y)
        if self.translate_start:
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
            if len(self.mandy):
                self.mandy[0].zoom = 3
            else:
                self.mandy.zoom = 6
            return True

        if cfg.key["mandy_reset"].matches(event):
            self.mandy.zoom = 6
            if len(self.mandy):
                self.mandy[0].zoom = 3
            self.mandy.rot = 0
            self.mandy.set_xy(-0.7, 0)
            self.mandy.set_jxy(0.0, 0)
            self.mandy.follow = -1
            self.parent.update()
            return True

        if cfg.key["mandy_pause"].matches(event):
            self.mandy.pause = not self.mandy.pause
            self.parent.update()
            return True

        if cfg.key["mandy_step"].matches(event):
            refr = not self.mandy.pause
            self.mandy.step()
            if refr:
                self.parent.update()
            return True

        if cfg.key["mandy_active"].matches(event):
            self.mandy.active = not self.mandy.active
            self.parent.update()
            return True

        if cfg.key["mandy_next"].matches(event):
            if self.mandy.follow < len(self.mandy) - 1:
                self.mandy.follow += 1
            else:
                self.mandy.follow = -1
            self.parent.update()
            return True

        if cfg.key["mandy_prev"].matches(event):
            if self.mandy.follow > -1:
                self.mandy.follow -= 1
            else:
                self.mandy.follow = len(self.mandy) - 1
            self.parent.update()
            return True

        if cfg.key["mandy_switch_mode"].matches(event):
            if not self.mandy.julia:
                self.mandy.follow = -1
            self.mandy.julia = not self.mandy.julia
            self.parent.update()

        if cfg.key["mandy_zero_julia"].matches(event):
            self.mandy.set_jxy(0, 0)

        if cfg.key["mandy_direction"].matches(event):
            self.mandy[0].speed *= -1
            self.parent.update()

        if cfg.key["mandy_pick_julia"].matches(event):
            if self.mandy.follow > -1:
                self.refollow = True
                self.mandy.follow = -1

            self.translate_start = self.last_xy
            self.translate_julia = True

        return False

    def on_key_release(self, widget, event):
        if cfg.key["mandy_pick_julia"].matches(event):
            self.translate_start = None
            self.translate_julia = False
            if self.refollow:
                self.mandy.follow = 0
                self.refollow = False

        return False

    def tick(self, wdg, param):
        nt = time.time_ns()

        t = (nt - self.last_t) / 1000000
        if t > 15:
            self.redraw()
            self.last_t = nt

        return True

    def on_enter(self, wdg, prm):
        self.entered = True
        self.grab_focus()
