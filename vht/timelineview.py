# timelineview.py - vahatraker
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

from vht import cfg, mod, extras
from datetime import datetime

import copy
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
        self.spl_dest = 0.02
        self.qb_start_dest = self.qb_start
        self.max_qb_start_dest = 23.0
        self.pointer_ry = 0
        self.pointer_ry_dest = 0
        self.playhead_ry = 0
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

        self.snap = 1

        self.fix_extras()

        self.snap_hold = False
        self.zoom_hold = False
        self.clone_hold = False

        self.moving = False
        self.resizing = False
        self.show_resize_handle = False
        self.resize_start = None
        self.gest_start_r = 0
        self.move_start_r = 0
        self.move_last_delta = 0

        self.move_start_x = 0
        self.move_x_delta = 0

        self.mouse_in_timeline = False
        self.mouse_in_changes = False

        self.moving_playhead = False

        self.moving_bpm = False
        self.highlight_change = None
        self.curr_change = None

        self.expanding = False
        self.exp_start = None
        self.exp_min = None
        self.exp_last_delta = 0

        self.curr_col = -1
        self.curr_strip_id = -1

        self.del_id = -1
        self.del_time_start = 0
        self.del_progress = 0.0

        self.highlight_loop = False
        self.mouse_in_loop = False
        self.drawing_loop = False
        self.drawing_loop_active = False
        self.drawing_loop_fallback = None
        self.mouse_loop_nearest = -1

        self.hint = None
        self.hint_alpha = 0
        self.hint_time_start = 0
        self.resize_curs = Gdk.Cursor.new_from_name(
            mod.mainwin.get_display(), "row-resize"
        )

        self.follow = False  # just for timeline export for now

    def fix_extras(self):
        if "timeline_zoom" in mod.extras:
            self.spl_dest = mod.extras["timeline_zoom"]
        else:
            mod.extras["timeline_zoom"] = self.spl_dest

        if "timeline_pos" in mod.extras:
            self.qb_start_dest = mod.extras["timeline_pos"]
        else:
            mod.extras["timeline_pos"] = self.qb_start_dest

        if "timeline_snap" in mod.extras:
            self.snap = mod.extras["timeline_snap"]
        else:
            mod.extras["timeline_snap"] = self.snap

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

    def highlight_alignment(self, y):
        colour = cfg.timeline_colour
        w = self.get_allocated_width()
        cr = self._context

        cr.set_line_width(3.0)
        cr.set_source_rgb(*(col * 0.7 for col in colour))
        cr.move_to(0, y)
        cr.line_to(w, y)
        cr.stroke()

    def redraw(self):
        cr = self._context

        if not cr:
            return

        w = self.get_allocated_width()
        h = self.get_allocated_height()
        *_, dx, _ = cr.text_extents("dupa")
        tw = mod.mainwin.seqlist_butts.get_allocated_width()

        hjust = mod.mainwin.seqlist_sw.get_hadjustment()

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

        # loop points
        cr.save()

        col = cfg.star_colour if mod.timeline.loop.active else cfg.timeline_colour
        i = (
            cfg.intensity_txt_highlight
            if self.highlight_loop
            else cfg.intensity_txt * 0.7
        )

        cr.set_source_rgb(*(c * i for c in col))
        cr.set_line_width(1)

        lsr = -1
        ler = -1
        ll = 5

        if mod.timeline.loop.start > -1:
            lsr = (
                mod.timeline.qb2t(mod.timeline.loop.start)
                - mod.timeline.qb2t(self.qb_start)
            ) / self.spl

        if mod.timeline.loop.end > -1:
            ler = (
                mod.timeline.qb2t(mod.timeline.loop.end)
                - mod.timeline.qb2t(self.qb_start)
            ) / self.spl

        if mod.timeline.loop.start > -1 and mod.timeline.loop.end > -1:
            xx = w - self._txt_height * 1.2

            cr.move_to(w - tw / 2, lsr)
            cr.line_to(xx, lsr)
            cr.line_to(xx, lsr + ll)
            cr.fill()

            cr.move_to(w - tw, lsr)
            cr.line_to(xx, lsr)
            cr.stroke()

            cr.move_to(w - tw / 2, ler)
            cr.line_to(xx, ler)
            cr.line_to(xx, ler - ll)
            cr.fill()

            cr.move_to(w - tw, ler)
            cr.line_to(xx, ler)
            cr.stroke()

            cr.set_line_width(2)

            cr.move_to(xx, lsr)
            cr.line_to(xx, ler)
            cr.stroke()

        cr.restore()

        # ticks -----------------
        ltim = -1
        sl = mod.timeline.length

        txtend = "%d:%02d:%02d" % (sl // 60, sl % 60, (sl * 100) % 100)
        *_, txtenddx, _ = cr.text_extents(txtend)
        nomorelaby = ((sl - tstart) / self.spl) - txtenddx * 1.5
        cr.set_source_rgb(*(col * cfg.intensity_txt for col in cfg.timeline_colour))
        do_draw = True
        for y in range(int(h)):
            if not do_draw:
                break

            tim = tstart + y * self.spl
            if math.floor(tim) == ltim:
                continue

            ltim = math.floor(tim)

            t = math.floor(tim % 60)
            x = w - self._txt_height
            txt = "%d:%02d" % (tim // 60, tim % 60)

            if tim > sl:
                do_draw = False
                continue

            if t == 0:
                cr.set_line_width(3)
                cr.move_to(w - tw, y)
                cr.line_to((w - tw) + tw * 0.5, y)
                cr.stroke()
                if y < nomorelaby:
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

        x = w - self._txt_height
        y = (sl - tstart) / self.spl

        if y <= h:
            cr.set_line_width(3)
            cr.move_to(w - tw, y)
            cr.line_to((w - tw) + tw * 0.5, y)
            cr.stroke()

            if tstart == 0:
                y = max(y, txtenddx * 2)

            self.insert_label(cr, x, y - txtenddx / 2, txtend)

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

        # timechanges
        cr.set_source_rgb(*(cfg.star_colour))
        cr.set_line_width(2)

        for t in mod.timeline.changes:
            rr = (
                mod.timeline.qb2t(t.row) - mod.timeline.qb2t(self.qb_start)
            ) / self.spl
            xx = w - tw

            # cr.move_to(xx, rr)
            rad = 6 if self.highlight_change == t else 4

            cr.arc(xx, rr, rad, 0, math.pi * 2)
            if t.linked:
                cr.fill()
            else:
                cr.stroke()

            if t == self.curr_change:
                cr.save()
                cr.set_line_width(1)
                cr.arc(xx, rr, rad * 1.5, 0, math.pi * 2)
                cr.stroke()
                cr.restore()

        # timechange insert indicator
        if (
            self.mouse_in_changes
            and self.zoom_hold
            and self.pointer_r <= mod.timeline.nqb
        ):
            if not mod.timeline.changes.get_at_qb(self.pointer_r):
                rr = (
                    mod.timeline.qb2t(self.pointer_r) - mod.timeline.qb2t(self.qb_start)
                ) / self.spl

                xx = w - tw
                cr.arc(xx, rr, 2, 0, math.pi * 2)
                cr.fill()

        # grid
        cr.save()
        cr.rectangle(0, 0, w - (tw + self.scrollbar_width * 1.5), h)
        cr.clip()

        mtx = cairo.Matrix()
        mtx.translate(-hjust.props.value, 0)
        cr.set_matrix(mtx)
        cw = mod.mainwin.seqlist._txt_height * cfg.mixer_padding
        for r in range(len(mod)):
            cr.set_source_rgb(*(col * 0.4 for col in cfg.timeline_colour))
            cr.set_line_width(1)
            cr.move_to(((r + 1) * cw) - (cw * 0.1), 0)
            cr.line_to(((r + 1) * cw) - (cw * 0.1), h)
            cr.stroke()

        cr.set_line_width(0.5)

        tstart = mod.timeline.qb2t(self.qb_start)
        tend = tstart + h * self.spl
        qbend = mod.timeline.t2qb(tend)

        mod_curr = mod.curr_seq

        cstr = None
        if self.curr_strip_id > -1 and (self.moving or self.resizing):
            cstr = mod.timeline.strips[self.curr_strip_id]

        # print(self.qb_start, qbend, tend)
        for stid, st in enumerate(mod.timeline.strips):
            if st.start > qbend:
                continue
            if st.length + st.start < self.qb_start:
                continue

            ystart = (mod.timeline.qb2t(st.start) - tstart) / self.spl

            yend = (mod.timeline.qb2t(st.start + st.length) - tstart) / self.spl
            lend = (
                mod.timeline.qb2t(st.start + math.ceil(st.seq.relative_length))
                - tstart  # st.seq.relative_length
            ) / self.spl

            yend -= ystart
            lend -= ystart

            thx = st.col * cw
            thxx = cw * 0.8

            if st.col == 0:
                thx += cw * 0.05
                thxx = cw * 0.75

            ind = st.seq.index
            colour = cfg.timeline_colour
            if type(mod_curr) is tuple:
                if mod_curr[1] == stid:
                    colour = cfg.star_colour

            alph = 0.7
            if st.seq.playing:
                alph = 0.9

            if not st.enabled:
                alph = 0.5

            if stid == self.curr_strip_id:
                if self.del_id == stid:
                    cr.set_source_rgb(
                        *(
                            col * alph * (1.0 - self.del_progress)
                            for col in cfg.timeline_colour
                        )
                    )
                else:
                    cr.set_source_rgb(*(col * alph for col in colour))
            else:
                cr.set_source_rgb(*(col * alph / 2 for col in colour))

            cr.rectangle(thx, ystart, thxx, min(yend, lend))
            cr.fill()

            thumb = mod.thumbmanager.get(ind)
            if thumb:
                thsurf = thumb.get_surface()

                thw, thh = thsurf.get_width(), thsurf.get_height()
                mtx = cairo.Matrix()
                # mtx.scale(thw / thxx, thh / yend)
                mtx.scale(thw / thxx, thh / lend)
                mtx.translate(-thx, -ystart)
                thumb.set_matrix(mtx)
                cr.set_source(thumb)
                cr.rectangle(thx, ystart, thxx, min(yend, lend))
                cr.fill()

            cr.set_line_width(1.5)
            cr.set_source_rgb(*(col * alph for col in colour))

            if stid == self.del_id:
                cr.rectangle(thx, ystart, thxx, yend - (yend * self.del_progress))
                cr.stroke()
            else:
                cr.rectangle(thx, ystart, thxx, min(yend, lend))
                cr.stroke()

                if st.length > math.ceil(st.seq.relative_length):
                    cr.move_to(thx + thxx / 2, ystart + lend)
                    cr.line_to(thx + thxx / 2, ystart + yend)
                    cr.stroke()
                    cr.move_to(thx, ystart + yend - 1)
                    cr.line_to(thx + thxx, ystart + yend - 1)
                    cr.set_line_width(3.0)
                    cr.stroke()
                    if yend - lend > 14:
                        cr.move_to(thx, ystart + yend - 5)
                        cr.line_to(thx + thxx, ystart + yend - 5)
                        cr.set_line_width(1.0)
                        cr.stroke()

                        cr.arc(
                            thx + (thxx * 0.3),
                            ystart + yend - 10,
                            2,
                            0,
                            2 * math.pi,
                        )
                        cr.fill()
                        cr.arc(
                            thx + (thxx * 0.7),
                            ystart + yend - 10,
                            2,
                            0,
                            2 * math.pi,
                        )
                        cr.fill()

                    # loop lines
                    ll = st.seq.relative_length * 2
                    while ll < st.length:
                        yyy = (mod.timeline.qb2t(st.start + ll) - tstart) / self.spl
                        cr.move_to(thx, yyy)
                        cr.line_to(thx + thxx, yyy)
                        cr.set_line_width(1.0)
                        cr.stroke()

                        ll += st.seq.relative_length

            if not st.enabled:
                cr.set_line_width(3.0)
                cr.set_source_rgb(*(col * 0.9 for col in colour))
                xo = thxx / 4
                lend = min(yend, lend)
                yo = lend / 4

                cr.move_to(thx + xo, ystart + yo)
                cr.line_to(thx + thxx - xo, ystart + lend - yo)
                cr.stroke()
                cr.move_to(thx + thxx - xo, ystart + yo)
                cr.line_to(thx + xo, ystart + lend - yo)
                cr.stroke()

            # highlight alignment
            if cstr and cstr != st:
                line = -1
                if st.start == cstr.start:
                    line = ystart

                if st.start + st.length == cstr.start:
                    line = ystart + yend

                if st.start + st.seq.relative_length == cstr.start:
                    line = ystart + lend

                if st.start + st.seq.relative_length == cstr.start + cstr.length:
                    line = ystart + lend

                if st.start == cstr.start + cstr.length:
                    line = ystart

                if st.start + st.length == cstr.start + cstr.length:
                    line = ystart + yend

                if line:
                    self.highlight_alignment(line)

            if self.hint:
                if self.hint[0] == st.start:
                    self.highlight_alignment(ystart)
                if self.hint[0] == st.start + st.length:
                    self.highlight_alignment(ystart + yend)
                if self.hint[0] == st.start + st.seq.relative_length:
                    self.highlight_alignment(ystart + lend)
                if self.hint[0] + self.hint[1] == st.start:
                    self.highlight_alignment(ystart)
                if self.hint[0] + self.hint[1] == st.start + st.length:
                    self.highlight_alignment(ystart + yend)
                if self.hint[0] + self.hint[1] == st.start + st.seq.relative_length:
                    self.highlight_alignment(ystart + lend)

            if self.drawing_loop:
                ls = mod.timeline.loop.start
                le = mod.timeline.loop.end

                if ls == st.start:
                    self.highlight_alignment(ystart)
                if ls == st.start + st.length:
                    self.highlight_alignment(ystart + yend)
                if le == st.start:
                    self.highlight_alignment(ystart)
                if le == st.start + st.length:
                    self.highlight_alignment(ystart + yend)

        cr.restore()

        # hint
        if self.curr_col > -1 and self.hint:
            ystart = (mod.timeline.qb2t(self.hint[0]) - tstart) / self.spl
            yend = (mod.timeline.qb2t(self.hint[0] + self.hint[1]) - tstart) / self.spl
            yend -= ystart

            thx = self.curr_col * cw
            thxx = cw * 0.8

            if self.curr_col == 0:
                thx += cw * 0.05
                thxx = cw * 0.75

            cr.set_line_width(1.0)
            cr.set_source_rgba(*(cfg.timeline_colour), self.hint_alpha * 0.8)
            cr.rectangle(thx, ystart, thxx, yend)
            cr.stroke()

        # pointer -------------------
        if self.pointer_xy:
            ry = self.pointer_ry

            cr.set_source_rgb(
                *(col * cfg.intensity_txt * 0.8 for col in cfg.star_colour)
            )
            cr.set_line_width(1)
            cr.move_to(0, ry)
            cr.line_to(w, ry)
            cr.stroke()

            t = mod.timeline.qb2t(min(self.pointer_r, mod.timeline.nqb))
            pr = min(self.pointer_r, mod.timeline.nqb)

            if self.moving:
                pr = mod.timeline.strips[self.curr_strip_id].start
                t = mod.timeline.qb2t(pr)

            if self.resizing:
                strp = mod.timeline.strips[self.curr_strip_id]
                pr = strp.start + strp.length
                t = mod.timeline.qb2t(pr)

            if self.expanding:
                pr = self.exp_start + self.exp_last_delta
                t = mod.timeline.qb2t(pr)

            if self.moving_bpm:
                pr = min(mod.timeline.nqb, self.curr_change.row)
                t = mod.timeline.qb2t(pr)

            if self.moving_playhead or self.drawing_loop:
                pr = max(pr, 0)

            lbl = "%d %d:%02d:%02d %.2f " % (
                pr,
                t // 60,
                t % 60,
                (t * 100) % 100,
                mod.timeline.bpm_at_qb(pr),
            )

            lblextra = ""
            # lblextra = " %d %d" % (ry, nomorelaby)

            if self.snap_hold:
                lblextra = lblextra + "snap: %d " % self.snap
            elif self.zoom_hold:
                lblextra = lblextra + "zoom: %.3f " % (self.spl * h)

            if self.resizing:
                strp = mod.timeline.strips[self.curr_strip_id]
                lblextra = lblextra + "length: %d " % (strp.length)

            if self.expanding:
                lblextra = lblextra + "shift: %d " % (self.exp_last_delta)

            margx = 20
            margy = 7
            *_, txtdy, txtdx, _ = cr.text_extents(lbl)
            txtw = txtdx
            *_, txtdx, _ = cr.text_extents(lblextra)
            txtw = max(txtw, txtdx)

            if h - ry < txtw:
                margy -= txtw + margy

            ty = ry + margy
            tx = w - (tw + margx)

            cr.save()
            cr.set_source_rgb(0, 0, 0)
            cr.move_to(tx + 2, ty + 2)
            cr.rotate(math.pi / 2.0)
            cr.show_text(lbl)
            cr.restore()

            cr.save()
            cr.set_source_rgb(
                *(col * cfg.intensity_txt_highlight for col in cfg.timeline_colour)
            )
            cr.move_to(tx, ty)
            cr.rotate(math.pi / 2.0)
            cr.show_text(lbl)
            cr.restore()

            if len(lblextra):
                ty = ry + margy
                tx = w - (tw + txtdy + (margx * 1.3))
                cr.save()
                cr.set_source_rgb(
                    *(col * cfg.intensity_txt_highlight for col in cfg.timeline_colour)
                )
                cr.move_to(tx, ty)
                cr.rotate(math.pi / 2.0)
                cr.show_text(lblextra)
                cr.restore()

        # play head
        ry = self.playhead_ry

        cr.set_source_rgb(
            *(col * cfg.intensity_txt * 0.8 for col in cfg.timeline_colour)
        )

        cr.set_line_width(1)
        cr.move_to(0, ry)
        cr.line_to(w - (tw * 0.9), ry)
        cr.stroke()

        ts = tw / 7.0

        cr.move_to(w - tw - ts, ry)
        cr.line_to(w - tw, ry - ts)
        cr.line_to(w - tw, ry + ts)
        cr.fill()

        self.get_window().invalidate_rect(None, False)

    def on_draw(self, widget, cr):
        cr.set_source_surface(self._surface, 0, 0)
        cr.paint()
        return True

    def on_button_press(self, widget, event):
        # filter double clicks
        if event.button == 2:
            if (
                event.type == Gdk.EventType._2BUTTON_PRESS
                or event.type == Gdk.EventType._3BUTTON_PRESS
            ):
                return

        # reset loop
        if self.highlight_loop:
            if event.button == cfg.delete_button:
                if (
                    mod.timeline.loop.start == 0
                    and mod.timeline.loop.end == mod.timeline.nqb
                ):
                    strp = (
                        mod.timeline.strips[mod.curr_seq[1]]
                        if type(mod.curr_seq) is tuple
                        else None
                    )
                    if strp:
                        mod.timeline.loop.start = strp.start
                        mod.timeline.loop.end = strp.start + strp.length
                else:
                    mod.timeline.loop.start = 0
                    mod.timeline.loop.end = mod.timeline.nqb
                return

            if event.button == 2:
                mod.timeline.loop.active = not mod.timeline.loop.active
                return

        # draw loop
        if (
            self.mouse_in_timeline
            and not self.clone_hold
            and not self.highlight_change
            and event.button == cfg.select_button
            and not self.zoom_hold
        ):
            self.drawing_loop_active = mod.timeline.loop.active
            self.drawing_loop_fallback = (
                mod.timeline.loop.start,
                mod.timeline.loop.end,
            )

            self.drawing_loop = True

            if self.mouse_loop_nearest == -1:
                self.gest_start_r = self.pointer_r

                mod.timeline.loop.active = False
                mod.timeline.loop.start = mod.timeline.loop.end = self.gest_start_r
                return
            elif self.mouse_loop_nearest == 1:
                self.gest_start_r = mod.timeline.loop.end
                mod.timeline.loop.active = False
                return
            elif self.mouse_loop_nearest == 2:
                self.gest_start_r = mod.timeline.loop.start
                mod.timeline.loop.active = False
                return

        if event.button == 2:
            if self.curr_strip_id > -1:  # disable
                strp = mod.timeline.strips[self.curr_strip_id]
                en = not strp.enabled

                if event.state & Gdk.ModifierType.CONTROL_MASK:
                    for strp in mod.timeline.strips:
                        if strp.seq.parent == self.curr_col:
                            strp.enabled = en
                else:
                    strp.enabled = en

                return True

            # playpos
            if not self.hint or not event.state & Gdk.ModifierType.CONTROL_MASK:
                self.moving_playhead = True
                mod.timeline.pos = self.pointer_r
                return

        if not self.moving_bpm:
            self.curr_change = None

        if (
            self.curr_strip_id == -1
            and event.button == cfg.select_button
            and self.clone_hold
        ):
            self.expanding = True
            self.hint = None
            self.gest_start_r = self.pointer_r
            self.exp_start = self.pointer_r
            self.exp_last_delta = 0
            self.exp_min = -mod.timeline.expand_start(self.exp_start)
            return

        # add change
        if (
            self.mouse_in_changes
            and event.button == cfg.select_button
            and self.zoom_hold
        ):
            tc = mod.timeline.changes.get_at_qb(self.pointer_r)
            if not tc and self.pointer_r <= mod.timeline.nqb:
                bpm = mod.timeline.bpm_at_qb(self.pointer_r)
                lnk = mod.timeline.interpol_at_qb(self.pointer_r)
                chg = mod.timeline.changes.insert(bpm, self.pointer_r, lnk)
                self.curr_change = mod.timeline.changes.get_at_qb(self.pointer_r)
                return

        # select change
        if (
            self.mouse_in_changes
            and event.button == cfg.select_button
            and not self.zoom_hold
        ):
            self.curr_change = (
                self.highlight_change
            )  # mod.timeline.changes.get_at_qb(self.pointer_r)
            if self.curr_change:
                if self.curr_change.row == 0:
                    return

                self.moving_bpm = True
                self.gest_start_r = self.curr_change.row
                self.move_start_r = self.curr_change.row
                self.move_last_delta = 0

        if (
            self.mouse_in_changes
            and self.highlight_change
            and event.button == cfg.select_button
            and (event.type == Gdk.EventType._2BUTTON_PRESS)
        ):
            if self.highlight_change.row > 0:
                self.highlight_change.linked = not self.highlight_change.linked
            return

        if self.moving_bpm:
            return

        # del change
        if (
            self.mouse_in_changes
            and event.button == cfg.delete_button
            and self.highlight_change
        ):
            delid = 0
            for did, chg in enumerate(mod.timeline.changes):
                if chg == self.highlight_change:
                    delid = did

            if delid > 0:
                del mod.timeline.changes[delid]

            self.curr_change = self.highlight_change = None

        if self.resizing or self.moving:
            return

        # del strip
        currs = mod.curr_seq[1] if type(mod.curr_seq) is tuple else -1
        if (
            event.button == cfg.delete_button
            and not self.resizing
            and not self.moving
            and not self.show_resize_handle
        ):
            if self.curr_strip_id > -1:
                self.del_id = self.curr_strip_id
                self.del_time_start = datetime.now()
                self.del_progress = 0.0

        if (
            event.button == cfg.delete_button
            and not self.resizing
            and not self.moving
            and self.show_resize_handle
        ):
            if self.curr_strip_id > -1:
                strp = mod.timeline.strips[self.curr_strip_id]
                strp.length = strp.seq.relative_length
                self.show_resize_handle = False
                self.get_window().set_cursor(None)

        if event.button != cfg.select_button and event.button != 2:
            return False

        if (
            self.scrollbar_highlight
            and self.scrollstart == -1
            and event.button == cfg.select_button
        ):
            self.scrollstart = event.y
            self.scrollstart_qb = self.qb_start
            return True

        if event.button == cfg.select_button and self.curr_strip_id > -1:
            if self.show_resize_handle:
                self.resizing = True
                self.resize_start = mod.timeline.strips[self.curr_strip_id].length
                self.gest_start_r = self.pointer_r
                return True

            if self.zoom_hold:
                src = mod.timeline.strips[self.curr_strip_id].seq
                seq = mod.timeline.strips.insert_clone(self.curr_strip_id).seq
                idx = seq.index

                extras.fix_extras_new_seq(idx)

                self.curr_strip_id = idx[1]

                mod.mainwin.sequence_view.switch(
                    mod.timeline.strips[self.curr_strip_id].seq.index
                )

                self.moving = True
                self.move_start_r = mod.timeline.strips[self.curr_strip_id].start
                self.gest_start_r = self.move_start_r
                self.move_last_delta = 0
                self.move_start_x = self.curr_col
                self.move_x_delta = 0
            else:
                mod.mainwin.sequence_view.switch(
                    mod.timeline.strips[self.curr_strip_id].seq.index
                )
                self.moving = True
                self.gest_start_r = self.pointer_r
                self.move_start_r = mod.timeline.strips[self.curr_strip_id].start
                self.move_last_delta = 0

            return True

        if self.curr_strip_id == -1 and self.curr_col > -1 and self.pointer_r > -1:
            rm = mod.timeline.room_at(self.curr_col, self.pointer_r)
            if rm >= mod[self.curr_col].relative_length or rm == -1:
                rr = int(min(self.pointer_r, mod.timeline.nqb))
                idx = None
                if self.zoom_hold:  # event.button == 1:  # empty
                    seq = mod.new_sequence(mod[self.curr_col].length)
                    strp = mod.timeline.strips.insert(
                        self.curr_col,
                        seq,
                        rr,
                        math.ceil(seq.relative_length),
                        seq.rpb,
                        seq.rpb,
                    )
                    strp.noteoffise()
                    if len(strp.seq) == 0:
                        if cfg.new_seqs_with_tracks:
                            strp.seq.add_track()

                    idx = strp.seq.index
                else:
                    seq = mod[self.curr_col]
                    idx = mod.timeline.strips.insert_parent(
                        self.curr_col,
                        rr,
                        math.ceil(seq.relative_length),
                        seq.rpb,
                        seq.rpb,
                    ).seq.index

                extras.fix_extras_new_seq(idx)

                mod.mainwin.sequence_view.switch(idx)

                self.curr_strip_id = idx[1]
                self.moving = True
                self.hint = False
                self.move_start_r = mod.timeline.strips[self.curr_strip_id].start
                self.gest_start_r = self.move_start_r

        return True

    def on_button_release(self, widget, event):
        self.moving_playhead = False

        if self.drawing_loop:
            self.drawing_loop = False
            if mod.timeline.loop.start == mod.timeline.loop.end:
                (
                    mod.timeline.loop.start,
                    mod.timeline.loop.end,
                ) = self.drawing_loop_fallback

            mod.timeline.loop.active = self.drawing_loop_active

        if self.moving:
            self.moving = False
            return

        if event.button == 2:
            return

        if event.button == cfg.delete_button:
            self.del_id = -1
            self.del_time_start = 0
            self.del_progress = 0.0
            return

        self.scrollstart = -1
        self.moving = False
        self.resizing = False
        self.expanding = False
        # self.curr_change = None
        self.highlight_change = None
        self.moving_bpm = False

        self.curr_strip_id = -1
        self.get_window().set_cursor(None)
        return True

    def on_motion(self, widget, event):
        w = self.get_allocated_width()
        h = self.get_allocated_height()

        tw = w - mod.mainwin.seqlist_butts.get_allocated_width()
        cw = mod.mainwin.seqlist._txt_height * cfg.mixer_padding
        col = event.x // cw

        if not self.moving:
            self.curr_col = -1 if col >= len(mod) else int(col)

        mod.mainwin.set_focus(self)
        if not self.drawing_loop:
            self.highlight_loop = False
        self.mouse_in_timeline = False
        self.mouse_in_changes = False

        if not self.moving_bpm:
            self.highlight_change = None

        if event.x > tw:
            self.mouse_in_timeline = True

        if abs(event.x - tw) < (w - tw) / 4:
            self.mouse_in_changes = True

        if (
            self.mouse_in_timeline
            and not self.mouse_in_changes
            and not self.moving_playhead
        ):
            self.mouse_in_loop = True
        else:
            self.mouse_in_loop = False

        if self.drawing_loop:
            s = self.gest_start_r
            e = self.gest_start_r

            if self.pointer_r == self.gest_start_r:
                mod.timeline.loop.start = mod.timeline.loop.end = s
            else:
                if self.pointer_r > self.gest_start_r:
                    e = self.pointer_r
                else:
                    s = self.pointer_r

                mod.timeline.loop.start = max(s, 0)
                mod.timeline.loop.end = min(e, mod.timeline.nqb)

        if self.expanding:
            xp = max(self.exp_min, self.pointer_r - self.gest_start_r)
            if xp != self.exp_last_delta:
                mod.timeline.expand(
                    self.exp_start + self.exp_last_delta, xp - self.exp_last_delta
                )

                self.exp_last_delta = xp

        if self.moving:
            delta = self.pointer_r - self.gest_start_r
            if self.move_last_delta != delta:
                snappos = mod.timeline.snap(self.curr_strip_id, delta)
                self.gest_start_r += (
                    snappos - mod.timeline.strips[self.curr_strip_id].start
                )
                mod.timeline.strips[self.curr_strip_id].start = snappos
                self.move_last_delta = delta

            if col != self.move_start_x and col < len(mod):
                cl = max(int(col), 0)
                strp = mod.timeline.strips[self.curr_strip_id]
                rm = mod.timeline.room_at(cl, strp.start)
                if rm >= strp.length or rm == -1:
                    strp.col = cl

                    self.move_start_x = strp.col

        if self.moving_bpm:
            delta = int(math.floor(self.pointer_r - self.gest_start_r))
            delta = round((delta / self.snap)) * self.snap
            if self.move_last_delta != delta:
                nrow = max(1, min(mod.timeline.nqb, self.move_start_r + delta))
                if not mod.timeline.changes.get_at_qb(nrow):
                    self.move_last_delta = delta
                    self.curr_change.row = nrow
                    self.curr_change = mod.timeline.changes.get_at_qb(nrow)
                    self.highlight_change = self.curr_change

        if self.resizing and self.curr_strip_id > -1:
            strp = mod.timeline.strips[self.curr_strip_id]
            delta = self.pointer_r - self.gest_start_r
            rm = mod.timeline.room_at(strp.col, strp.start, strp.seq.index[1])
            if rm == -1:
                rm = max(1, int(self.resize_start + delta))

            nl = min(rm, max(1, int((self.resize_start + delta))))

            strp.length = nl

            # loop hint
            if strp.length % int(strp.seq.relative_length) == 0:
                self.hint = strp.start + strp.length, strp.start + strp.length

        if self.scrollstart > -1:
            delta = (event.y - self.scrollstart) / ((h - self.scrollbar_height))
            delta *= self.max_qb_start_dest
            self.qb_start_dest = min(
                self.max_qb_start, max(0, self.scrollstart_qb + delta)
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

        if self.expanding:
            self.scrollbar_highlight = False

        self.pointer_xy = (event.x, event.y)

        if self.moving_playhead:
            mod.timeline.pos = max(self.pointer_r, 0)
            return

        r = mod.timeline.t2qb(
            self.l2t(self.pointer_xy[1]) + mod.timeline.qb2t(self.qb_start)
        )

        if not self.drawing_loop:
            self.show_resize_handle = False

        if self.mouse_in_loop:
            if not self.drawing_loop:
                self.show_resize_handle = False

            self.mouse_loop_nearest = -1
            tstart = mod.timeline.qb2t(self.qb_start)
            yend = (mod.timeline.qb2t(mod.timeline.loop.start) - tstart) / self.spl

            if abs(event.y - yend) < 5:
                self.show_resize_handle = True
                self.highlight_loop = True
                self.mouse_loop_nearest = 1

            yend = (mod.timeline.qb2t(mod.timeline.loop.end) - tstart) / self.spl

            if abs(event.y - yend) < 5:
                self.show_resize_handle = True
                self.highlight_loop = True
                self.mouse_loop_nearest = 2

        if not self.moving and not self.resizing:
            self.curr_strip_id = -1
            r = r if r else 0

            if self.curr_col > -1:
                i = mod.timeline.qb2s(self.curr_col, r)
                if i > -1:
                    self.curr_strip_id = i
                    strp = mod.timeline.strips[i]
                    tstart = mod.timeline.qb2t(self.qb_start)
                    yend = (
                        mod.timeline.qb2t(strp.start + strp.length) - tstart
                    ) / self.spl
                    offs_from_back = event.y - yend
                    if -5 <= offs_from_back:
                        self.show_resize_handle = True
                    else:
                        self.show_resize_handle = False

        if self.show_resize_handle or self.resizing:
            self.get_window().set_cursor(self.resize_curs)
        else:
            self.get_window().set_cursor(None)

        return True

    def on_leave(self, wdg, prm):
        if (
            not self.moving
            and not self.resizing
            and not self.expanding
            and not self.drawing_loop
        ):
            self.pointer_xy = None
            self.highlight_loop = False
            self.mouse_in_loop = False
            # self.pointer_r = -1
            self.curr_col = -1
            self.curr_strip_id = -1

        self.snap_hold = False
        self.clone_hold = False
        self.zoom_hold = False

        return True

    def on_enter(self, wdg, prm):
        return True

    def on_scroll(self, widget, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            self.zoom_hold = True

        if event.state & (Gdk.ModifierType.MOD1_MASK | Gdk.ModifierType.MOD5_MASK):
            self.snap_hold = True

        if event.state & Gdk.ModifierType.SHIFT_MASK:
            hjust = mod.mainwin.seqlist_sw.get_hadjustment()
            cw = mod.mainwin.seqlist._txt_height * cfg.mixer_padding
            if event.direction == Gdk.ScrollDirection.UP:
                hjust.props.value -= cw
                return True
            if event.direction == Gdk.ScrollDirection.DOWN:
                hjust.props.value += cw
                return True

        if self.snap_hold:
            if event.direction == Gdk.ScrollDirection.UP:
                if self.zoom_hold:
                    self.snap = min(self.snap + 1, 64)
                else:
                    self.snap = min(self.snap * 2, 64)

            if event.direction == Gdk.ScrollDirection.DOWN:
                if self.zoom_hold:
                    self.snap = max(self.snap - 1, 1)
                else:
                    self.snap = max(self.snap / 2, 1)

            mod.extras["timeline_snap"] = self.snap
            return True

        if self.zoom_hold:
            if event.direction == Gdk.ScrollDirection.UP:
                self.spl_dest = max(self.spl * 0.8, math.pow(0.5, 6))
                if type(mod.curr_seq) is tuple:
                    strp = mod.timeline.strips[mod.curr_seq[1]]
                    self.qb_start_dest = max(0, strp.start - (strp.length / 2))

            if event.direction == Gdk.ScrollDirection.DOWN:
                self.spl_dest = min(self.spl / 0.8, 0.25)

            mod.extras["timeline_zoom"] = self.spl_dest
            return True

        if event.direction == Gdk.ScrollDirection.UP:
            self.qb_start_dest = max(self.qb_start - self.row_scroll, 0)
        if event.direction == Gdk.ScrollDirection.DOWN:
            self.qb_start_dest = min(self.qb_start + self.row_scroll, self.max_qb_start)

        mod.extras["timeline_pos"] = self.qb_start_dest
        return True

    def on_key_press(self, widget, event):
        # print(Gdk.keyval_name(Gdk.keyval_to_lower(event.keyval)), event.keyval)
        if event.keyval == 65513:  # alt
            self.snap_hold = True

        if 65507 <= event.keyval <= 65508:  # ctrl
            self.zoom_hold = True

        if 65505 <= event.keyval <= 65506:  # shift
            self.clone_hold = True

        return mod.mainwin.sequence_view.on_key_press(widget, event)

    def on_key_release(self, widget, event):
        self.zoom_hold = False
        self.clone_hold = False
        self.snap_hold = False

        return mod.mainwin.sequence_view.on_key_release(widget, event)

    def animate(self):
        self.curr_col = min(len(mod) - 1, self.curr_col)

        self.qb_start = max(0, min(self.qb_start, self.max_qb_start))
        self.qb_start_dest = max(0, min(self.qb_start_dest, self.max_qb_start))

        if self.qb_start_dest - self.qb_start != 0:
            self.qb_start += (self.qb_start_dest - self.qb_start) / 4

        if self.spl_dest - self.spl != 0:
            self.spl += (self.spl_dest - self.spl) / 5

        if abs(self.max_qb_start_dest - self.max_qb_start) > 0.01:
            self.max_qb_start += (self.max_qb_start_dest - self.max_qb_start) / 3

        if self.pointer_ry_dest - self.pointer_ry != 0:
            self.pointer_ry += (self.pointer_ry_dest - self.pointer_ry) / 1.5

        if self.pointer_xy:
            self.pointer_r = mod.timeline.t2qb(
                self.l2t(self.pointer_xy[1]) + mod.timeline.qb2t(self.qb_start)
            )

            if not self.moving_bpm:
                self.pointer_r = math.floor((self.pointer_r / self.snap)) * self.snap

            if self.mouse_in_changes and not self.moving_bpm:
                self.highlight_change = mod.timeline.changes.get_at_qb(
                    self.pointer_r, 3
                )

        rr = self.pointer_r

        if self.curr_strip_id > -1:
            strp = mod.timeline.strips[self.curr_strip_id]
            if self.moving:
                rr = strp.start
            elif self.resizing:
                rr = strp.start + strp.length

        if self.expanding:
            rr = self.exp_start + self.exp_last_delta

        if self.moving_bpm:
            rr = self.curr_change.row

        if self.mouse_in_changes and self.highlight_change and not self.moving_bpm:
            rr = self.highlight_change.row
            self.pointer_r = rr

        self.pointer_ry_dest = max(
            (
                mod.timeline.qb2t(min(rr, mod.timeline.nqb))
                - mod.timeline.qb2t(self.qb_start)
            )
            / self.spl,
            0,
        )

        self.playhead_ry = (
            mod.timeline.qb2t(mod.timeline.pos) - mod.timeline.qb2t(self.qb_start)
        ) / self.spl

        if self.follow:
            if self.playhead_ry < self.qb_start_dest:
                self.qb_start_dest = mod.timeline.pos - 1

            if self.playhead_ry > self.get_allocated_height() * 0.333:
                self.qb_start_dest = mod.timeline.pos + 1

        if not self.drawing_loop:
            if self.mouse_loop_nearest == -1:
                self.highlight_loop = False

            if self.mouse_in_loop:
                ls = mod.timeline.loop.start
                le = mod.timeline.loop.end
                if self.pointer_r >= ls and self.pointer_r <= le:
                    self.highlight_loop = True

        hint = None

        if self.moving or self.resizing or self.expanding:
            return

        if self.zoom_hold and self.curr_strip_id > -1:
            strp = mod.timeline.strips[self.curr_strip_id]
            rm = mod.timeline.place_clone(self.curr_strip_id)
            hint = (rm, strp.length)
        else:
            if self.curr_strip_id == -1 and self.curr_col > -1:
                rm = mod.timeline.room_at(self.curr_col, self.pointer_r)
                if rm >= mod[self.curr_col].relative_length or rm == -1:
                    hint = (
                        min(self.pointer_r, mod.timeline.nqb),
                        math.ceil(mod[self.curr_col].relative_length),
                    )

        if hint != self.hint:
            self.hint = hint
            self.hint_alpha = 0
            self.hint_time_start = datetime.now()

        if self.hint:
            t = datetime.now() - self.hint_time_start
            t = float(t.seconds) + t.microseconds / 1000000
            self.hint_alpha = min(t / cfg.timeline_hint_time, 1.0)

        if self.del_id > -1:
            t = datetime.now() - self.del_time_start
            t = float(t.seconds) + t.microseconds / 1000000

            self.del_progress = t / cfg.timeline_delete_time
            if self.del_progress > 1.0:
                did = self.del_id
                self.del_id = -1
                self.curr_strip_id = -1
                if cfg.autosave_seq:
                    mod.mainwin.app.autosave()
                mod.mainwin.gui_del_seq(mod.timeline.strips[did].seq.index)

                self.del_time_start = 0
                self.del_progress = 0

    def tick(self):
        self.animate()
        self.redraw()
        return True
