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

from vht import cfg, mod

import math
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
            | Gdk.EventMask.ENTER_NOTIFY_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
            | Gdk.EventMask.KEY_RELEASE_MASK
        )

        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.on_button_release)
        self.connect("motion-notify-event", self.on_motion)
        self.connect("key-press-event", self.on_key_press)
        self.connect("key-release-event", self.on_key_release)
        self.connect("scroll-event", self.on_scroll)
        self.connect("draw", self.on_draw)
        self.connect("configure-event", self.on_configure)
        self.connect("leave-notify-event", self.on_leave)
        self.connect("enter-notify-event", self.on_enter)

        self.set_can_focus(True)

        self._surface = None
        self._context = None

        self.spl = 0.5  # seconds per line (on screen)
        self.qb_start = 0
        self.max_qb_start = 23.0
        self.spl_dest = 0.015625
        self.qb_start_dest = self.qb_start
        self.max_qb_start_dest = 23.0
        self.pointer_ry = 0
        self.pointer_ry_dest = 0

        self.scrollbar_height = 23
        self.scrollbar_width = 8
        self.scrollbar_pos = 0
        self.scrollbar_highlight = False
        self.scrollstart = -1
        self.scrollstart_qb = -1

        self.song_length = mod.timeline.length
        self.time_height = 23

        self.pointer_xy = None
        self.pointer_r = -1

        self.snap = 8
        self.snap_hold = False
        self.zoom_hold = False

        self.curr_col = -1

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
            cfg.timeline_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD
        )
        self._context.set_font_size(cfg.timeline_font_size)

        (q, w, e, self._txt_height, r, t) = self._context.text_extents("|")
        (y, u, i, o, self._txt_width, p) = self._context.text_extents("0")

        self.redraw()

    def l2t(self, l):
        return l * self.spl

    def insert_label(self, cr, x, y, t):
        cr.save()
        *_, dx, _ = cr.text_extents(t)
        y = max(0, y - dx / 2)
        cr.set_source_rgb(
            *(col * cfg.intensity_txt * 0.8 for col in cfg.timeline_colour)
        )
        cr.move_to(x, y)
        cr.rotate(math.pi / 2.0)
        cr.show_text(t)
        cr.restore()

    def redraw(self):
        cr = self._context

        if not cr:
            return

        w = self.get_allocated_width()
        h = self.get_allocated_height()
        *_, dx, _ = cr.text_extents("dupa")
        tw = mod.mainwin.seqlist_butts.get_allocated_width()

        # timeline -------------------

        cr.set_source_rgb(
            *(col * cfg.intensity_background for col in cfg.timeline_colour)
        )
        cr.rectangle(0, 0, w, h)
        cr.fill()

        cr.set_source_rgb(*(col * cfg.intensity_txt for col in cfg.timeline_colour))
        cr.set_line_width(1)
        cr.move_to(w - tw, 0)
        cr.line_to(w - tw, h)
        cr.stroke()

        tstart = mod.timeline.qb2t(self.qb_start)

        self.time_height = h * self.spl
        self.row_scroll = mod.timeline.t2qb(self.time_height * 0.23)
        self.max_qb_start_dest = mod.timeline.t2qb(
            mod.timeline.length - (self.time_height * 0.7)
        )

        if not self.max_qb_start_dest:
            self.max_qb_start_dest = 0.0

        self.scrollbar_height = h * (self.time_height / mod.timeline.length)
        self.scrollbar_pos = (h - self.scrollbar_height) * (
            self.qb_start / self.max_qb_start
        )

        if self.scrollbar_highlight:
            cr.set_source_rgb(
                *(col * cfg.intensity_txt_highlight for col in cfg.timeline_colour)
            )
        else:
            cr.set_source_rgb(*(col * cfg.intensity_txt for col in cfg.timeline_colour))

        cr.set_line_width(1)
        if self.scrollbar_height < h:
            cr.rectangle(
                w - tw, self.scrollbar_pos, -self.scrollbar_width, self.scrollbar_height
            )
            cr.fill()

        # ticks -----------------
        ltim = -1
        sl = mod.timeline.length

        txtend = "%d:%02d:%02d" % (sl // 60, sl % 60, (sl * 100) % 100)
        *_, txtenddx, _ = cr.text_extents(txtend)
        nomorelaby = ((sl - tstart) / self.spl) - txtenddx * 1.5
        cr.set_source_rgb(*(col * cfg.intensity_txt for col in cfg.timeline_colour))
        do_draw = True
        for y in range(h):
            if not do_draw:
                break

            tim = tstart + y * self.spl
            if math.floor(tim) == ltim:
                continue

            ltim = math.floor(tim)

            t = math.floor(tim % 60)
            x = w - self._txt_height
            txt = "%d:%02d" % (tim // 60, tim % 60)

            if tim >= sl:
                tim = sl

                x = w - self._txt_height
                y = (sl - tstart) / self.spl

                cr.set_line_width(3)
                cr.move_to(w - tw, y)
                cr.line_to((w - tw) + tw * 0.5, y)
                cr.stroke()

                if tstart == 0:
                    y = max(y, txtenddx * 2)
                self.insert_label(cr, x, y - txtenddx / 2, txtend)
                do_draw = False
                continue

            if t == 0:
                cr.set_line_width(3)
                cr.move_to(w - tw, y)
                cr.line_to((w - tw) + tw * 0.5, y)
                cr.stroke()
                self.insert_label(cr, x, y, txt)
            elif t % 30 == 0:
                cr.set_line_width(2)
                cr.move_to(w - tw, y)
                cr.line_to((w - tw) + tw * 0.4, y)
                cr.stroke()
                if y < nomorelaby:
                    self.insert_label(cr, x, y, txt)
            elif t % 15 == 0:
                cr.set_line_width(2)
                cr.move_to(w - tw, y)
                cr.line_to((w - tw) + tw * 0.3, y)
                cr.stroke()
                if y < nomorelaby:
                    self.insert_label(cr, x, y, txt)
            elif t % 5 == 0:
                cr.set_line_width(0.75)
                cr.move_to(w - tw, y)
                cr.line_to((w - tw) + tw * 0.3, y)
                cr.stroke()
            else:
                cr.set_line_width(0.5)
                cr.move_to(w - tw, y)
                cr.line_to((w - tw) + tw * 0.2, y)
                cr.stroke()

        # snapticks -----------------
        r = int(math.floor(self.qb_start))
        rr = (mod.timeline.qb2t(r) - mod.timeline.qb2t(self.qb_start)) / self.spl
        cr.set_source_rgb(
            *(col * cfg.intensity_txt * 0.7 for col in cfg.timeline_colour)
        )
        lrr = -420
        drw = True
        while rr < h and r < mod.timeline.nqb + 1:
            if drw:
                cr.set_line_width(1)
                cr.move_to(w - tw, rr)
                cr.line_to((w - tw) - self.scrollbar_width, rr)
                cr.stroke()
                lrr = rr

            drw = False
            r += 1
            rr = (mod.timeline.qb2t(r) - mod.timeline.qb2t(self.qb_start)) / self.spl
            if r % self.snap == 0:
                if rr - lrr > 1:
                    drw = True

        # grid
        cr.save()
        cw = mod.mainwin.seqlist._txt_height * cfg.mixer_padding
        for r in range(len(mod)):
            cr.set_source_rgb(*(col * 0.6 for col in cfg.timeline_colour))
            cr.set_line_width(1)
            cr.move_to((r + 1) * cw, 0)
            cr.line_to((r + 1) * cw, h)
            cr.stroke()

        cr.set_line_width(0.5)

        tstart = mod.timeline.qb2t(self.qb_start)
        tend = tstart + h * self.spl
        qbend = mod.timeline.t2qb(tend)

        # print(self.qb_start, qbend, tend)
        for st in mod.timeline.strips:
            if st.start > qbend:
                continue
            if st.loop_length + st.start < self.qb_start:
                continue

            ystart = (mod.timeline.qb2t(st.start) - tstart) / self.spl
            yend = mod.timeline.qb2t(st.length) / self.spl
            lend = mod.timeline.qb2t(st.loop_length) / self.spl

            if st.col == self.curr_col:
                cr.set_source_rgb(*(col * 0.5 for col in cfg.timeline_colour))
            else:
                cr.set_source_rgb(*(col * 0.4 for col in cfg.timeline_colour))

            cr.rectangle(st.col * cw + 1, ystart, cw - 2, yend)
            cr.fill()

            thumb = mod.thumbmanager.get(st.seq.index)
            if thumb:
                thsurf = thumb.get_surface()
                thx = st.col * cw + 1

                thw, thh = thsurf.get_width(), thsurf.get_height()
                mtx = cairo.Matrix()
                mtx.scale(thw / (cw - 2), thh / yend)
                mtx.translate(-thx, -ystart)
                thumb.set_matrix(mtx)
                cr.set_source(thumb)
                cr.rectangle(thx, ystart, cw - 2, yend)
                cr.fill()

            cr.set_source_rgb(*(col * 0.2 for col in cfg.timeline_colour))
            cr.rectangle(st.col * cw + 1, ystart, cw - 2, yend)
            cr.stroke()

        # pointer -------------------
        if self.pointer_xy:
            ry = self.pointer_ry

            cr.set_source_rgb(
                *(col * cfg.intensity_txt * 0.6 for col in cfg.timeline_colour)
            )
            cr.set_line_width(1)
            cr.move_to(0, ry)
            cr.line_to(w, ry)
            cr.stroke()

            t = mod.timeline.qb2t(self.pointer_r)
            lbl = "%d %d:%02d:%02d" % (self.pointer_r, t // 60, t % 60, (t * 100) % 100)
            lblextra = ""

            if self.snap_hold:
                lblextra = lblextra + "snap: %d" % self.snap
            elif self.zoom_hold:
                lblextra = lblextra + "zoom: %.3f" % (self.spl * h)

            margx = 20
            margy = 7
            *_, txtdy, txtdx, _ = cr.text_extents(lbl)

            ty = ry + margy
            tx = w - (tw + margx)

            cr.save()
            cr.set_source_rgb(*(col * cfg.intensity_txt for col in cfg.timeline_colour))
            cr.move_to(tx, ty)
            cr.rotate(math.pi / 2.0)
            cr.show_text(lbl)
            cr.restore()

            if len(lblextra):
                ty = ry + margy
                tx = w - (tw + txtdy + margx + margy)
                cr.save()
                cr.set_source_rgb(
                    *(col * cfg.intensity_txt_highlight for col in cfg.timeline_colour)
                )
                cr.move_to(tx, ty)
                cr.rotate(math.pi / 2.0)
                cr.show_text(lblextra)
                cr.restore()

        wnd = self.get_window()
        wnd.invalidate_rect(None, False)

    def on_draw(self, widget, cr):
        cr.set_source_surface(self._surface, 0, 0)
        cr.paint()
        return True

    def on_button_press(self, widget, event):
        if self.scrollbar_highlight and self.scrollstart == -1:
            self.scrollstart = event.y
            self.scrollstart_time = mod.timeline.qb2t(self.qb_start)
            return True

        if self.curr_col > -1 and self.pointer_r > -1:
            seq = mod[self.curr_col]
            mod.timeline.strips.insert(
                self.curr_col,
                int(self.pointer_r),
                seq.length,
                seq.rpb,
                seq.rpb,
                seq.length,
            )

        return True

    def on_button_release(self, widget, event):
        self.scrollstart = -1
        return True

    def on_motion(self, widget, event):
        w = self.get_allocated_width()
        h = self.get_allocated_height()

        tw = w - mod.mainwin.seqlist_butts.get_allocated_width()
        cw = mod.mainwin.seqlist._txt_height * cfg.mixer_padding
        col = event.x // cw
        self.curr_col = -1 if col >= len(mod) else int(col)

        mod.mainwin.set_focus(self)

        if self.scrollstart > -1:
            desttime = (
                self.scrollstart_time
                + (event.y - self.scrollstart)
                / (h - self.scrollbar_height)
                * mod.timeline.length
            )

            self.qb_start_dest = min(
                self.max_qb_start, mod.timeline.t2qb(max(desttime, 0))
            )
            self.pointer_xy = None
            return True

        if (
            tw - self.scrollbar_width < event.x < tw
            and self.scrollbar_pos
            < event.y
            < self.scrollbar_pos + self.scrollbar_height
        ):
            self.scrollbar_highlight = True
        else:
            self.scrollbar_highlight = False

        self.pointer_xy = (event.x, event.y)

        return True

    def on_leave(self, wdg, prm):
        self.pointer_xy = None
        self.pointer_r = -1
        return True

    def on_enter(self, wdg, prm):
        return True

    def on_scroll(self, widget, event):
        if event.state & Gdk.ModifierType.SHIFT_MASK:
            if event.direction == Gdk.ScrollDirection.UP:
                self.snap = min(self.snap * 2, 32)
            if event.direction == Gdk.ScrollDirection.DOWN:
                self.snap = max(self.snap / 2, 1)
            return True

        if event.state & Gdk.ModifierType.CONTROL_MASK:
            if event.direction == Gdk.ScrollDirection.UP:
                self.spl_dest = max(self.spl * 0.8, math.pow(0.5, 10))
            if event.direction == Gdk.ScrollDirection.DOWN:
                self.spl_dest = min(self.spl / 0.8, 0.25)
            return True

        if event.direction == Gdk.ScrollDirection.UP:
            self.qb_start_dest = max(self.qb_start - self.row_scroll, 0)
        if event.direction == Gdk.ScrollDirection.DOWN:
            self.qb_start_dest = min(self.qb_start + self.row_scroll, self.max_qb_start)
        return True

    def on_key_press(self, widget, event):
        # print(Gdk.keyval_name(Gdk.keyval_to_lower(event.keyval)), event.keyval)
        if 65505 <= event.keyval <= 65506:  # shift
            self.snap_hold = True

        if 65507 <= event.keyval <= 65508:  # ctrl
            self.zoom_hold = True

        return mod.mainwin.sequence_view.on_key_press(widget, event)

    def on_key_release(self, widget, event):
        if 65505 <= event.keyval <= 65506:  # shift
            self.snap_hold = False

        if 65507 <= event.keyval <= 65508:  # ctrl
            self.zoom_hold = False

        return mod.mainwin.sequence_view.on_key_release(widget, event)

    def animate(self):
        if self.qb_start_dest - self.qb_start != 0:
            self.qb_start += (self.qb_start_dest - self.qb_start) / 3

        if self.spl_dest - self.spl != 0:
            self.spl += (self.spl_dest - self.spl) / 10

        if abs(self.max_qb_start_dest - self.max_qb_start) > 0.01:
            self.max_qb_start += (self.max_qb_start_dest - self.max_qb_start) / 3

        if self.pointer_ry_dest - self.pointer_ry != 0:
            self.pointer_ry += (self.pointer_ry_dest - self.pointer_ry) / 2

        if self.pointer_xy:
            self.pointer_r = mod.timeline.t2qb(
                self.l2t(self.pointer_xy[1]) + mod.timeline.qb2t(self.qb_start)
            )

            if self.pointer_r < mod.timeline.nqb:
                self.pointer_r = round((self.pointer_r / self.snap)) * self.snap

            self.pointer_ry_dest = max(
                (mod.timeline.qb2t(self.pointer_r) - mod.timeline.qb2t(self.qb_start))
                / self.spl,
                0,
            )

    def tick(self):
        self.animate()
        self.redraw()
        return True
