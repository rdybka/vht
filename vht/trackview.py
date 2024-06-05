# trackview.py - vahatraker
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

from vht.controllerundobuffer import ControllerUndoBuffer
from vht.controllereditor import ControllerEditor
from vht.timeshifteditor import TimeshiftEditor
from vht.velocityeditor import VelocityEditor
from vht.probeditor import ProbEditor
from vht.poormanspiano import PoorMansPiano
from vht.trackundobuffer import TrackUndoBuffer
from vht.trackviewpointer import TrackviewPointer
from vht import mod, cfg
import math
import cairo

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk

# import inspect


class TrackView(Gtk.DrawingArea):
    track_views = []
    clipboard = {}

    @staticmethod
    def leave_all():
        for wdg in TrackView.track_views:
            redr = False
            if wdg.hover or wdg.edit or wdg.select_start:
                redr = True

            if wdg.pitchwheel_editor:
                wdg.pitchwheel_editor.undo_buff.add_state()
                if wdg.pitchwheel_editor.edit > -1 or wdg.pitchwheel_editor.selection:
                    redr = True

                if wdg.pitchwheel_editor.doodle_hint_row > -1:
                    redr = True

                wdg.pitchwheel_editor.selection = None
                wdg.pitchwheel_editor.edit = -1
                wdg.pitchwheel_editor.doodle_hint_row = -1

            for ctrl in wdg.controller_editors:
                ctrl.undo_buff.add_state()
                if ctrl.edit > -1 or ctrl.selection:
                    redr = True

                if ctrl.doodle_hint_row > -1:
                    redr = True

                ctrl.selection = None
                ctrl.edit = -1
                ctrl.doodle_hint_row = -1

            wdg.hover = None
            wdg.edit = None
            wdg.select_start = None
            wdg.select_end = None

            if redr:
                wdg.redraw()

    def __init__(self, seq, trk, parent):
        super(TrackView, self).__init__()

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
        self.connect("key-press-event", self.on_key_press)
        self.connect("key-release-event", self.on_key_release)
        self.connect("leave-notify-event", self.on_leave)
        self.connect("destroy", self.on_destroy)

        self.seq = seq
        self.trk = trk
        self.parent = parent
        self._pointer = TrackviewPointer(self, trk, seq)
        self.txt_width = 0
        self.txt_height = 0
        self.fld_width = 0
        self.width = 0
        self.height = 0
        self.spacing = 1.0
        self.pmp = PoorMansPiano(self.trk, self.seq)

        self.drag = False
        self.sel_drag = False
        self.sel_dragged = False
        self.sel_drag_prev = None
        self.sel_drag_back = None
        self.sel_drag_front = None
        self.sel_drag_start = 0
        self.drag_cloned = False
        self.select = False
        self.select_start = None
        self.select_end = None

        self.nudge_last_y = -1
        self.nudge_hide_timeshift = False
        self.nudge_buff = None

        self.keyboard_focus = None

        self.velocity_editor = None
        self.timeshift_editor = None
        self.prob_editor = None
        self.pitchwheel_editor = None
        self.controller_editors = []

        self.show_notes = True
        self.show_timeshift = False
        self.show_pitchwheel = False
        self.show_controllers = False
        self.show_probs = False

        self.extras = None

        if trk:
            self.extras = trk.extras
            self.undo_buff = TrackUndoBuffer(trk)

            self.show_timeshift = self.extras["track_show_timeshift"]
            self.show_pitchwheel = self.extras["track_show_pitchwheel"]
            self.show_controllers = self.extras["track_show_controllers"]
            self.show_notes = self.extras["track_show_notes"]
            self.show_probs = self.extras["track_show_probs"]

        self._surface = None
        self._context = None
        self._back_surface = None
        self._back_context = None

        self.zero_pattern_surface = None
        self.empty_pattern_surface = None
        self.zero_pattern_highlight = -1

        self.zero_pattern = None
        self.empty_pattern = None

        self.hover = None
        self.edit = None

        self.set_can_focus(True)

        TrackView.track_views.append(self)

    def __del__(self):
        if self._surface:
            self._surface.finish()

        if self._back_surface:
            self._back_surface.finish()

    def tick(self):
        if self._context and self._back_context:
            if self.trk:
                self._pointer.draw(self.trk.pos)
            else:
                self._pointer.draw(self.seq.pos)

        return True

    def configure(self):
        if self.trk:
            for cn, ctrl in enumerate(self.trk.ctrls):
                if ctrl == -1:
                    if not self.pitchwheel_editor:
                        self.pitchwheel_editor = ControllerEditor(self, cn)
                else:
                    append = True
                    for ed in self.controller_editors:
                        if ed.ctrlnum == cn:
                            append = False

                    if append:
                        self.controller_editors.append(ControllerEditor(self, cn))
                        # we could be called on the fly while recording so let's
                        # check the extras for new ctrls
                        if str(cn) not in self.extras["ctrl_names"]:
                            n = mod.ctrls[cfg.default_ctrl_name]
                            if ctrl in n:
                                self.extras["ctrl_names"][str(cn)] = (
                                    cfg.default_ctrl_name,
                                    n[ctrl],
                                )

        self._back_context.select_font_face(
            cfg.seq_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD
        )

        self._back_context.set_font_size(self.parent.font_size)

        w = self.get_allocated_width()
        h = self.get_allocated_height()

        cr = self._back_context
        crf = self._context
        crf.set_source_surface(self._back_surface)

        fld_txt = "000 "
        *_, self.fld_width, _ = cr.text_extents(fld_txt)

        row_txt = "000 000"
        if self.show_timeshift:
            row_txt += " 000"

        if self.show_probs:
            row_txt += " 000"

        row_txt += "|"
        (x, y, width, height, dx, dy) = cr.text_extents(row_txt)

        self.txt_height = float(height) * self.spacing * cfg.seq_spacing
        self.txt_width = int(dx)

        nw = 0
        if self.show_notes:
            nw = self.txt_width * len(self.trk)

        if self.velocity_editor:
            self.velocity_editor.precalc(cr)
            nw = nw + self.velocity_editor.width

        if self.prob_editor:
            self.prob_editor.precalc(cr)
            nw = nw + self.prob_editor.width

        if self.timeshift_editor:
            self.timeshift_editor.precalc(cr)
            nw = nw + self.timeshift_editor.width

        if self.pitchwheel_editor:
            self.pitchwheel_editor.precalc(cr, nw)
            if self.show_pitchwheel:
                nw = nw + self.pitchwheel_editor.width

        if self.show_controllers:
            for ctrl in self.controller_editors:
                ctrl.precalc(cr, nw)
                nw = nw + ctrl.width

        nh = (self.txt_height * self.trk.nrows) + 5
        self.set_size_request(nw, nh)
        self.width = nw
        self.height = nh

        if self.pitchwheel_editor:
            self.pitchwheel_editor.configure()

        for ctrl in self.controller_editors:
            ctrl.configure()

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

            if self.empty_pattern_surface:
                self.empty_pattern_surface.finish()

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

            # empty pattern
            empl = self.zero_pattern_highlight
            empl *= 1 + empl % 2  # oh yeah

            self.empty_pattern_surface = self._back_surface.create_similar(
                cairo.CONTENT_COLOR_ALPHA,
                round(self.width),
                math.ceil(self.txt_height * empl),
            )
            cr = cairo.Context(self.empty_pattern_surface)

            cr.select_font_face(
                cfg.seq_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD
            )
            cr.set_font_size(self.parent.font_size)

            for r in range(empl):
                even_high = cfg.even_highlight
                if not r % 2:
                    even_high = 1.0

                cr.set_source_rgb(
                    *(col * cfg.intensity_background * even_high for col in cfg.colour)
                )
                cr.rectangle(0, r * self.txt_height, self.width, self.txt_height)
                cr.fill()

                if self.zero_pattern_highlight > 1 and (r) % self.parent.highlight == 0:
                    cr.set_source_rgb(
                        *(col * cfg.intensity_txt_highlight for col in cfg.colour)
                    )
                else:
                    cr.set_source_rgb(*(col * cfg.intensity_txt for col in cfg.colour))

                for c in range(len(self.trk)):
                    xtraoffs = 0

                    if self.velocity_editor:
                        if c > self.velocity_editor.col:
                            xtraoffs = self.velocity_editor.width

                    if self.timeshift_editor:
                        if c > self.timeshift_editor.col:
                            xtraoffs = self.timeshift_editor.width

                    if self.prob_editor:
                        if c > self.prob_editor.col:
                            xtraoffs = self.prob_editor.width

                    (x, y, width, height, dx, dy) = cr.text_extents("0")
                    yy = (r + 1) * self.txt_height - ((self.txt_height - height) / 2.0)
                    cr.move_to((c * self.txt_width) + x + xtraoffs, yy)
                    cr.show_text("---")

            self.empty_pattern = cairo.SurfacePattern(self.empty_pattern_surface)
            self.empty_pattern.set_extend(cairo.Extend.REPEAT)
            matrix = cairo.Matrix()
            matrix.translate(0, 0)
            # because rowheight is float
            matrix.scale(
                1.0, math.ceil(self.txt_height * empl) / (self.txt_height * empl)
            )
            self.empty_pattern.set_matrix(matrix)

    def on_destroy(self, wdg):
        if self._surface:
            self._surface.finish()

        if self._back_surface:
            self._back_surface.finish()

        if self.zero_pattern_surface:
            self.zero_pattern_surface.finish()

        if self.empty_pattern_surface:
            self.empty_pattern_surface.finish()

        for ctrl in self.controller_editors:
            ctrl.destroy()

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

        rows_to_draw = []

        if complete:
            rows_to_draw = range(self.trk.nrows)
        else:
            for r in range(self.trk.nrows):
                if from_row <= r <= to_row:
                    rows_to_draw.append(r)

        if not complete:
            for r in rows_to_draw:
                ir.x = 0
                ir.width = w
                ir.y = r * self.txt_height
                ir.height = self.txt_height * 2
                crf.rectangle(ir.x, ir.y, ir.width, ir.height)
                crf.fill()
                wnd.invalidate_rect(ir, False)

        if complete:
            crf.paint()
            self.queue_draw()

    # reconfigure and redraw
    def redraw_full(self):
        # may be called before realising
        if not self._back_context:
            return

        oldw = self.keyboard_focus
        oldr = -1
        if oldw:
            oldr = oldw.edit

        self.keyboard_focus = None
        self.configure()
        self.redraw()

        if oldw:
            fnum = oldw.midi_ctrlnum

            for w in self.controller_editors + [self.pitchwheel_editor]:
                if w == oldw:
                    self.keyboard_focus = w
                    self.keyboard_focus.edit = oldr

        # who's calling?
        # cf = inspect.currentframe()
        # of = inspect.getouterframes(cf, 2)
        # for f in of:
        # 	print("redraw full", f[3], f[2], f[1])
        self.queue_draw()

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

        # normal view
        rows_to_draw = []
        if complete:
            if not ctrl:
                cr.set_source(self.zero_pattern)
                cr.set_source_rgb(
                    *(col * cfg.intensity_background for col in cfg.colour)
                )
                cr.rectangle(0, 0, w, h)
                cr.fill()
                # self.configure()
                self.trk.clear_updates()
            rows_to_draw = range(self.trk.nrows)
        else:
            for r in range(self.trk.nrows):
                if from_row <= r <= to_row:
                    rows_to_draw.append(r)

        if ctrl:
            for r in rows_to_draw:
                ctrl.draw(cr, r)
                ir.x = 0
                ir.width = w
                ir.y = r * self.txt_height
                ir.height = self.txt_height * 2
                crf.set_source_surface(self._back_surface)
                crf.rectangle(ir.x, ir.y, ir.width, ir.height)
                crf.fill()
                wnd.invalidate_rect(ir, False)

            if complete:
                crf.paint()
                self.queue_draw()

            return

        last_c = len(self.trk) - 1
        for c in range(len(self.trk)):
            for r in rows_to_draw:
                veled = 0
                tsed = 0
                probsed = 0
                xtraoffs = 0
                ed_width = 0

                sep = 0

                if self.velocity_editor:
                    ed_width = self.velocity_editor.width
                    if c == self.velocity_editor.col:
                        veled = self.velocity_editor.width
                    if c > self.velocity_editor.col:
                        xtraoffs = self.velocity_editor.width

                    sep = 1

                if self.timeshift_editor:
                    ed_width = self.timeshift_editor.width
                    if c == self.timeshift_editor.col:
                        tsed = self.timeshift_editor.width
                    if c > self.timeshift_editor.col:
                        xtraoffs = self.timeshift_editor.width

                    sep = 2

                if self.prob_editor:
                    ed_width = self.prob_editor.width
                    if c == self.prob_editor.col:
                        probsed = self.prob_editor.width
                    if c > self.prob_editor.col:
                        xtraoffs = self.prob_editor.width

                even_high = cfg.even_highlight
                if r % 2 == 0:
                    even_high = 1.0

                rw = self.trk[c][r]

                draw_text = True
                if rw.type == 0 and not (
                    self.hover and r == self.hover[1] and c == self.hover[0]
                ):
                    cr.set_source(self.empty_pattern)
                    draw_text = False
                else:
                    cr.set_source(self.zero_pattern)

                # print(xtraoffs, ed_width)

                if self.show_notes:
                    cr.rectangle(
                        c * self.txt_width + xtraoffs,
                        r * self.txt_height,
                        self.txt_width + 5 + ed_width,
                        self.txt_height,
                    )
                    cr.fill()

                if self.hover and r == self.hover[1] and c == self.hover[0]:
                    cr.set_source_rgb(
                        *(col * cfg.intensity_txt_highlight * 1.2 for col in cfg.colour)
                    )
                else:
                    if r % self.seq.rpb == 0:
                        cr.set_source_rgb(
                            *(col * cfg.intensity_txt_highlight for col in cfg.colour)
                        )
                    else:
                        cr.set_source_rgb(
                            *(col * cfg.intensity_txt for col in cfg.colour)
                        )

                show_selection = True
                if self.velocity_editor or self.timeshift_editor or self.prob_editor:
                    show_selection = False

                if (
                    self.show_notes
                    and show_selection
                    and self.select_start
                    and self.select_end
                ):
                    ssx = self.select_start[0]
                    ssy = self.select_start[1]
                    sex = self.select_end[0]
                    sey = self.select_end[1]

                    if sex < ssx:
                        sex, ssx = ssx, sex

                    if sey < ssy:
                        sey, ssy = ssy, sey

                    if ssx <= c <= sex and ssy <= r <= sey:
                        draw_text = True
                        cr.set_source_rgb(
                            *(col * cfg.intensity_select for col in cfg.colour)
                        )
                        if c == len(self.trk) - 1:
                            cr.rectangle(
                                c * self.txt_width,
                                r * self.txt_height,
                                (self.txt_width / 8.0) * 7.4,
                                self.txt_height,
                            )
                        else:
                            cr.rectangle(
                                c * self.txt_width,
                                r * self.txt_height,
                                self.txt_width,
                                self.txt_height,
                            )
                        cr.fill()
                        cr.set_source_rgb(
                            *(col * cfg.intensity_background for col in cfg.colour)
                        )

                if show_selection and not self.select_start and not self.select_end:
                    if (
                        self.show_notes
                        and self.edit
                        and r == self.edit[1]
                        and c == self.edit[0]
                    ):
                        draw_text = True
                        if mod.record == 0:
                            cr.set_source_rgb(*(cfg.record_colour))
                        else:
                            cr.set_source_rgb(*(cfg.colour))

                        if c == len(self.trk) - 1:
                            cr.rectangle(
                                c * self.txt_width + xtraoffs,
                                (r * self.txt_height) + self.txt_height * 0.1,
                                (self.txt_width / 8.0) * 7.4,
                                self.txt_height * 0.8,
                            )
                        else:
                            cr.rectangle(
                                c * self.txt_width + xtraoffs,
                                (r * self.txt_height) + self.txt_height * 0.1,
                                self.txt_width,
                                self.txt_height * 0.8,
                            )

                        cr.fill()
                        cr.set_source_rgb(
                            *(col * cfg.intensity_background for col in cfg.colour)
                        )

                if draw_text:
                    if sep == 0 or sep == 1:
                        (x, y, width, height, dx, dy) = cr.text_extents("000 0000")
                    else:
                        (x, y, width, height, dx, dy) = cr.text_extents("000 0000 000")

                    yy = (r + 1) * self.txt_height - ((self.txt_height - height) / 2)

                    cr.move_to((c * self.txt_width) + x + xtraoffs, yy)

                    ts_sign = "0"
                    if rw.delay > 0:
                        ts_sign = "+"
                    if rw.delay < 0:
                        ts_sign = "-"

                    if self.show_notes and (rw.type == 1 or rw.type == 2):
                        if rw.type == 1:
                            ltxt = "%3s %03d" % (str(rw), rw.velocity)
                        else:
                            ltxt = "%3s  " % (str(rw))

                        if rw.note == 127 and self.trk.channel == 16 and mod.pnq_hack:
                            ltxt = "pnq /o\\"

                        rtxt = ""

                        if self.show_timeshift:
                            tstxt = "%c%02d" % (ts_sign, abs(rw.delay))
                            if sep == 0 or sep == 2:
                                ltxt += " " + tstxt
                            elif sep == 1:
                                rtxt = tstxt

                        if self.show_probs:
                            prtxt = "%03d" % (100 - rw.prob)
                            if sep == 0:
                                ltxt += " " + prtxt
                            elif sep == 1:
                                if self.show_timeshift:
                                    rtxt += " "

                                rtxt += prtxt
                            elif sep == 2:
                                rtxt = prtxt

                        cr.show_text(ltxt)
                        if rtxt:
                            if sep == 1:
                                cr.move_to(
                                    (c * self.txt_width)
                                    + dx
                                    + xtraoffs
                                    + self.velocity_editor.width,
                                    yy,
                                )

                            if sep == 2:
                                cr.move_to(
                                    (c * self.txt_width)
                                    + dx
                                    + xtraoffs
                                    + self.timeshift_editor.width,
                                    yy,
                                )

                            cr.show_text(rtxt)

                    if rw.type == 0:  # none
                        cr.show_text("---    ")

                (x, y, width, height, dx, dy) = cr.text_extents("0")

                if veled and (rw.type == 1 or self.velocity_editor.line > -1):
                    self.velocity_editor.draw(cr, c, r, rw)

                if tsed and 0 < rw.type < 3:
                    self.timeshift_editor.draw(cr, c, r, rw)

                if probsed and 0 < rw.type < 3:
                    self.prob_editor.draw(cr, c, r, rw)

                if c == len(self.trk) - 1:
                    if self.show_pitchwheel:
                        self.pitchwheel_editor.draw(cr, r)

                    if self.show_controllers:
                        for ctrl in self.controller_editors:
                            ctrl.draw(cr, r)

                if not complete:
                    if c == last_c:
                        (x, y, width, height, dx, dy) = cr.text_extents("0")
                        cr.set_source_rgb(
                            *(col * cfg.intensity_lines for col in cfg.colour)
                        )
                        cr.set_line_width(
                            (self.parent.font_size / 6.0) * cfg.seq_line_width
                        )
                        cr.move_to(self.width - (width / 2), 0)
                        cr.line_to(
                            self.width - (width / 2), (self.trk.nrows) * self.txt_height
                        )
                        cr.stroke()

                    ir.x = 0
                    ir.width = w
                    ir.y = r * self.txt_height
                    ir.height = self.txt_height * 2
                    crf.rectangle(ir.x, ir.y, ir.width, ir.height)
                    crf.fill()
                    wnd.invalidate_rect(ir, False)

        if complete:
            (x, y, width, height, dx, dy) = cr.text_extents("0")
            cr.set_source_rgb(*(col * cfg.intensity_lines for col in cfg.colour))
            cr.set_line_width((self.parent.font_size / 6.0) * cfg.seq_line_width)
            cr.move_to(self.width - (width / 2), 0)
            cr.line_to(self.width - (width / 2), (self.trk.nrows) * self.txt_height)
            cr.stroke()

            crf.paint()
            self.queue_draw()

    def on_draw(self, widget, cr):
        cr.set_source_surface(self._surface, 0, 0)
        cr.paint()
        return False

    def swap_row(self, col, row, col2, row2):
        rw = self.trk[col][row]
        rw2 = self.trk[col2][row2]
        rw3 = self.trk[col][row]
        rw.copy(rw2)
        rw2.copy(rw3)

    def on_scroll(self, event):
        if self.show_notes and not self.keyboard_focus and self.edit:
            old = self.edit[1]
            self.edit = (
                int(self.edit[0]),
                int(min(max(0, self.edit[1] + event.delta_y), self.trk.nrows - 1)),
            )

            self.redraw(old)
            self.redraw(self.edit[1])
            self.parent.autoscroll_req = True
            return True

        if self.show_pitchwheel:
            if self.pitchwheel_editor.on_scroll(event):
                return True

        if self.show_controllers:
            for ctrl in self.controller_editors:
                if ctrl.on_scroll(event):
                    return True

        return False

    def on_motion(self, widget, event):
        if not self.trk:
            return False

        if not event.window.get_toplevel().get_state() & Gdk.WindowState.FOCUSED:
            return False

        for wdg in self.parent.prop_view._track_box.get_children() + [
            self.parent._side_prop
        ]:
            if wdg.get_realized():
                if self != wdg.popover:
                    if wdg.popped:
                        return

        new_hover_row = min(int(event.y / self.txt_height), self.trk.nrows - 1)
        new_hover_column = min(int(event.x / self.txt_width), len(self.trk) - 1)

        new_hover_row = max(new_hover_row, 0)
        new_hover_column = max(new_hover_column, 0)

        if self.velocity_editor:
            if self.velocity_editor.hover_row == -1 and not (
                (event.state & Gdk.ModifierType.SHIFT_MASK)
                and (event.state & Gdk.ModifierType.BUTTON1_MASK)
            ):
                return self.velocity_editor.on_motion(widget, event)

            if self.velocity_editor.hover_row > -1:
                return self.velocity_editor.on_motion(widget, event)

        if self.timeshift_editor and not (
            (event.state & Gdk.ModifierType.CONTROL_MASK)
            and (event.state & Gdk.ModifierType.BUTTON1_MASK)
        ):
            return self.timeshift_editor.on_motion(widget, event)

        if self.prob_editor and not (
            (event.state & Gdk.ModifierType.CONTROL_MASK)
            and (event.state & Gdk.ModifierType.BUTTON1_MASK)
        ):
            return self.prob_editor.on_motion(widget, event)

        oldf = self.keyboard_focus

        if event.x < self.txt_width * len(self.trk):
            if self.keyboard_focus:
                if self.keyboard_focus.edit == -1:
                    self.keyboard_focus = None

                if self.keyboard_focus:
                    if self.keyboard_focus.selection:
                        return

        if self.show_pitchwheel:
            self.pitchwheel_editor.on_motion(widget, event)

        if self.show_controllers:
            for ctrl in self.controller_editors:
                ctrl.on_motion(ctrl, event)

        if oldf != self.keyboard_focus:
            if oldf:
                dh = oldf.doodle_hint_row
                oldf.doodle_hint_row = -1
                self.redraw(dh)

            self.parent.prop_view.redraw(self.trk.index)

        if self.select:
            if not self.select_start:
                self.select_start = self.edit
                self.select_end = self.select_start

            if (
                self.select_end[1] != new_hover_row
                or self.select_end[0] != new_hover_column
            ):
                self.select_end = new_hover_column, new_hover_row
                self.redraw()

        if (
            self.select_start
            and self.select_end
            and (event.state & Gdk.ModifierType.CONTROL_MASK)
            and (not event.state & Gdk.ModifierType.SHIFT_MASK)
            and (event.state & Gdk.ModifierType.BUTTON1_MASK)
        ):  # nudge time
            if self.nudge_last_y == -1:
                self.nudge_last_y = event.y
                if not self.show_timeshift:
                    self.nudge_hide_timeshift = True
                    self.show_timeshift = True

                self.timeshift_editor = TimeshiftEditor(
                    self, new_hover_column, new_hover_row, event
                )
                self.timeshift_editor.confirmed = True
                self.configure()
                self.parent.redraw_track(self.trk)
                self.nudge_buff = {}
                self.sel_dragged = True
                return True

            n = math.floor(event.y - self.nudge_last_y) / 4
            if n != 0:
                maxn = -50
                minn = 50

                for c in range(self.select_start[0], self.select_end[0] + 1):
                    for r in range(self.select_start[1], self.select_end[1] + 1):
                        if not (c, r) in self.nudge_buff:
                            self.nudge_buff[(c, r)] = self.trk[c][r].delay

                        if self.trk[c][r].type > 0:
                            maxn = max(maxn, self.nudge_buff[(c, r)])
                            minn = min(minn, self.nudge_buff[(c, r)])

                maxn = 49 - maxn
                minn = -49 - minn

                if n > 0:
                    n = min(n, maxn)
                else:
                    n = max(n, minn)

                for c in range(self.select_start[0], self.select_end[0] + 1):
                    for r in range(self.select_start[1], self.select_end[1] + 1):
                        self.trk[c][r].delay = self.nudge_buff[(c, r)] + n
                        self.redraw(r)

            return True

        if (
            self.select_start
            and self.select_end
            and (event.state & Gdk.ModifierType.SHIFT_MASK)
            and (event.state & Gdk.ModifierType.CONTROL_MASK)
            and (event.state & Gdk.ModifierType.BUTTON1_MASK)
        ):  # velocity
            if self.nudge_last_y == -1:
                self.nudge_last_y = event.y

                self.velocity_editor = VelocityEditor(
                    self, new_hover_column, new_hover_row, event
                )
                self.velocity_editor.confirmed = True
                self.configure()
                self.parent.redraw_track(self.trk)
                self.nudge_buff = {}
                self.sel_dragged = True
                return True

            n = -math.floor(event.y - self.nudge_last_y) / 4
            if n != 0:
                maxn = 0
                minn = 127

                for c in range(self.select_start[0], self.select_end[0] + 1):
                    for r in range(self.select_start[1], self.select_end[1] + 1):
                        if self.trk[c][r].type == 1:
                            if not (c, r) in self.nudge_buff:
                                self.nudge_buff[(c, r)] = self.trk[c][r].velocity
                            maxn = max(maxn, self.nudge_buff[(c, r)])
                            minn = min(minn, self.nudge_buff[(c, r)])

                maxn = 127 - maxn
                minn = -minn

                if n > 0:
                    n = min(n, maxn)
                else:
                    n = max(n, minn)

                for c in range(self.select_start[0], self.select_end[0] + 1):
                    for r in range(self.select_start[1], self.select_end[1] + 1):
                        if (c, r) in self.nudge_buff:
                            self.trk[c][r].velocity = self.nudge_buff[(c, r)] + n
                            self.redraw(r)

            return True

        if self.drag:
            self.parent.autoscroll_req = True
            if (
                self.trk[new_hover_column][new_hover_row].type == 0
            ):  # dragging single cell
                if self.edit[1] != new_hover_row or self.edit[0] != new_hover_column:
                    old_row = self.edit[1]
                    olr = self.trk[self.edit[0]][self.edit[1]]
                    self.swap_row(
                        self.edit[0], self.edit[1], new_hover_column, new_hover_row
                    )

                    if self.drag_cloned:
                        olr.copy(self.trk[new_hover_column][new_hover_row])
                        self.drag_cloned = False

                    self.edit = new_hover_column, new_hover_row

                    self.redraw(new_hover_row)
                    self.redraw(old_row)

        if self.sel_drag:  # dragging selection
            dx = new_hover_column - self.sel_drag_prev[0]
            dy = new_hover_row - self.sel_drag_prev[1]
            sw = self.select_end[0] - self.select_start[0]
            sh = self.select_end[1] - self.select_start[1]

            if sh > self.trk.nrows / 2:
                self.parent.autoscroll_req = False
            else:
                self.parent.autoscroll_req = True

            if sh == self.trk.nrows - 1:  # rotate
                if sw == len(self.trk) - 1:
                    self.sel_dragged = True
                    nx = self.select_start[0]
                    ny = self.select_start[1] + dy

                    for r in self.sel_drag_front:
                        nc = r[0] + nx, r[1] + ny

                        if nc[1] > self.trk.nrows - 1:
                            nc = nc[0], nc[1] - self.trk.nrows

                        if nc[1] < 0:
                            nc = nc[0], nc[1] + self.trk.nrows

                        rr = self.sel_drag_front[r]
                        self.trk[nc[0]][nc[1]].type = rr[0]
                        self.trk[nc[0]][nc[1]].note = rr[1]
                        self.trk[nc[0]][nc[1]].velocity = rr[2]
                        self.trk[nc[0]][nc[1]].delay = rr[3]

                    self.redraw()
                    self.parent.prop_view.redraw(-1)
                    return False

            if dx or dy:
                self.sel_dragged = True
                nx = self.select_start[0] + dx
                ny = self.select_start[1] + dy

                self.sel_drag_prev = new_hover_column, new_hover_row
                old = self.select_start[1], self.select_end[1]

                for r in self.sel_drag_front:
                    nc = r[0] + self.select_start[0], r[1] + self.select_start[1]
                    if self.select_start[1] > self.select_end[1]:
                        nc = r[0] + self.select_end[0], r[1] + self.select_end[1]

                    inbounds = True
                    if (
                        nc[0] < 0
                        or nc[0] > len(self.trk) - 1
                        or nc[1] < 0
                        or nc[1] > self.trk.nrows - 1
                    ):
                        inbounds = False

                    if inbounds:
                        if nc in self.sel_drag_back:
                            rr = self.sel_drag_back[nc]
                            self.trk[nc[0]][nc[1]].type = rr[0]
                            self.trk[nc[0]][nc[1]].note = rr[1]
                            self.trk[nc[0]][nc[1]].velocity = rr[2]
                            self.trk[nc[0]][nc[1]].delay = rr[3]
                        else:
                            self.trk[nc[0]][nc[1]].clear()

                self.select_start = nx, ny
                self.select_end = nx + sw, ny + sh

                for r in self.sel_drag_front:
                    nc = r[0] + nx, r[1] + ny
                    if self.select_end[1] < self.select_start[1]:
                        nc = r[0] + self.select_end[0], r[1] + self.select_end[1]

                    inbounds = True

                    if (
                        nc[0] < 0
                        or nc[0] > len(self.trk) - 1
                        or nc[1] < 0
                        or nc[1] > self.trk.nrows - 1
                    ):
                        inbounds = False

                    if inbounds:
                        rr = self.sel_drag_front[r]
                        if rr[0]:
                            self.trk[nc[0]][nc[1]].type = rr[0]
                            self.trk[nc[0]][nc[1]].note = rr[1]
                            self.trk[nc[0]][nc[1]].velocity = rr[2]
                            self.trk[nc[0]][nc[1]].delay = rr[3]

                self.redraw()

            self.edit = self.select_end

        oh = self.hover
        self.hover = new_hover_column, int(event.y / self.txt_height)
        if self.hover[1] >= self.trk.nrows:
            self.hover = None

        if self.hover != oh:
            if oh:
                self.redraw(oh[1])

            if self.hover:
                self.redraw(self.hover[1])

        if mod.active_track:
            if not mod.active_track == self:
                if not mod.active_track.edit:
                    for c in mod.active_track.controller_editors + [
                        mod.active_track.pitchwheel_editor
                    ]:
                        if c.edit > -1 and not c.selection:
                            return False

                    self.parent.change_active_track(self)
        else:
            self.parent.change_active_track(self)

        return False

    def on_button_press(self, widget, event):
        if not self.trk:
            return False

        # self.parent.autoscroll_req = False

        mod.clear_popups()

        shift = False
        if event.state & Gdk.ModifierType.SHIFT_MASK:
            shift = True

        row = int(event.y / self.txt_height)
        col = int(event.x / self.txt_width)
        offs = int(event.x) % int(self.txt_width)

        # pitchwheel/controllers
        if col >= len(self.trk) or self.show_notes is False:
            if self.show_pitchwheel:
                if (
                    event.x > self.pitchwheel_editor.x_from
                    and event.x < self.pitchwheel_editor.x_to
                ):
                    self.pitchwheel_editor.on_button_press(widget, event)

            if self.show_controllers:
                for ctrl in self.controller_editors:
                    if event.x > ctrl.x_from and event.x < ctrl.x_to:
                        ctrl.on_button_press(widget, event)
            return False

        if (event.button == cfg.delete_button or row >= self.trk.nrows) and row >= 0:
            trk = mod.active_track

            if row >= self.trk.nrows:
                if trk:
                    mod.record = 0
                    self.leave_all()
                    self.parent.redraw_track(mod.active_track.trk)
                    self.select = None
                self.parent.change_active_track(self)
                return True

            if self.trk[col][row].type == 0:
                if trk:
                    mod.record = 0
                    self.leave_all()
                    self.parent.redraw_track(mod.active_track.trk)
                    self.select = None
                    self.hover = col, row
                self.parent.change_active_track(self)
                return True

            flds = 2
            if self.show_timeshift:
                flds += 1

            if self.show_probs:
                flds += 1

            fldwidth = self.txt_width / flds

            if fldwidth < offs < fldwidth * 2:  # reset velocity
                if 0 < self.trk[col][row].type < 2:
                    self.velocity_editor = VelocityEditor(self, col, row, event)
                    self.velocity_editor.clearing = True
                    self.trk[col][row].velocity = cfg.velocity
                    self.trk[col][row].velocity_range = 0

                    self.configure()
                    self.redraw()
                    self.parent.prop_view.redraw()
                    self.undo_buff.add_state()
                    return True

            if self.show_timeshift:
                if fldwidth * 2 < offs < fldwidth * 3:  # reset timeshift
                    if 0 < self.trk[col][row].type < 3:
                        self.timeshift_editor = TimeshiftEditor(self, col, row, event)
                        self.timeshift_editor.clearing = True
                        self.trk[col][row].delay = 0
                        self.trk[col][row].delay_range = 0

                        self.configure()
                        self.redraw()
                        self.parent.prop_view.redraw()
                        self.undo_buff.add_state()
                        return True

            if self.show_probs:
                fld = 2
                if self.show_timeshift:
                    fld += 1

                if fldwidth * fld < offs < fldwidth * (fld + 1):  # reset probs
                    if 0 < self.trk[col][row].type < 3:
                        self.prob_editor = ProbEditor(self, col, row, event)
                        self.prob_editor.clearing = True
                        self.trk[col][row].prob = 0

                        self.configure()
                        self.redraw()
                        self.parent.prop_view.redraw()
                        self.undo_buff.add_state()
                        return True

            self.trk[col][row].clear()
            self.redraw(row)
            self.undo_buff.add_state()
            return True

        enter_edit = False

        if event.button != cfg.select_button and event.button != 2:
            return False

        if row >= self.trk.nrows:
            return False

        self.sel_drag = False
        self.sel_dragged = False
        if event.button == cfg.select_button:
            if self.select_start:
                ssx = self.select_start[0]
                ssy = self.select_start[1]
                sex = self.select_end[0]
                sey = self.select_end[1]

                if sex < ssx:
                    sex, ssx = ssx, sex

                if sey < ssy:
                    sey, ssy = ssy, sey

                if ssx <= col <= sex:
                    if ssy <= row <= sey:
                        self.sel_drag = True
                        self.sel_drag_prev = col, row
                        self.sel_drag_start = self.select_start[1]

                        self.sel_drag_front = self.to_dict(True)
                        self.sel_drag_back = self.to_dict()

                        for r in self.sel_drag_front:
                            del self.sel_drag_back[(r[0] + ssx, r[1] + ssy)]

                        return True

            if not self.trk[col][row].type:  # empty
                enter_edit = True
                if not shift:
                    self.select = True
                    self.select_start = None
                    self.select_end = None

            if self.trk[col][row].type in (1, 2):  # note_on
                enter_edit = True
                self.drag = True

                if event.state & Gdk.ModifierType.CONTROL_MASK:
                    self.drag_cloned = True
        else:
            if event.state & Gdk.ModifierType.CONTROL_MASK:
                return False

        flds = 2
        if self.show_timeshift:
            flds += 1

        if self.show_probs:
            flds += 1

        fldwidth = self.txt_width / flds
        if offs < fldwidth and event.button == cfg.select_button:
            enter_edit = True
        elif (
            offs < fldwidth * 2 and self.trk[col][row].type == 2
        ) and event.button == cfg.select_button:
            enter_edit = True
        else:
            if not shift and 0 < self.trk[col][row].type < 3:
                enter_edit = False
                self.drag = False

                if fldwidth < offs < fldwidth * 2 and self.trk[col][row].type == 1:
                    self.velocity_editor = VelocityEditor(self, col, row, event)

                if self.show_timeshift:
                    if fldwidth * 2 < offs < fldwidth * 3:
                        self.timeshift_editor = TimeshiftEditor(self, col, row, event)

                    if self.show_probs and event.button == cfg.select_button:
                        if fldwidth * 3 < offs < fldwidth * 4:
                            self.prob_editor = ProbEditor(self, col, row, event)

                elif self.show_probs and event.button == cfg.select_button:
                    if fldwidth * 2 < offs < fldwidth * 3:
                        self.prob_editor = ProbEditor(self, col, row, event)

                self.configure()
                self.redraw()
                self.parent.prop_view.redraw()
                self.undo_buff.add_state()

        if enter_edit and event.button == cfg.select_button:
            if shift:
                self.select_end = col, row
                if self.select_start:
                    self.select = True

                if self.edit:  # new selection
                    self.select = True
                    self.select_start = self.edit
                    self.select_end = col, row

                self.redraw()
                return True

            TrackView.leave_all()
            self.parent.change_active_track(self)
            self.keyboard_focus = None
            self.parent.autoscroll_req = True
            self.parent.prop_view.redraw(self.trk.index)
            olded = self.edit
            self.edit = col, row
            self.redraw(row)

            if olded:
                self.redraw(olded[1])
            return True

        return True

    def on_button_release(self, widget, event):
        # pitchwheel/controllers
        if self.show_pitchwheel:
            self.pitchwheel_editor.on_button_release(widget, event)

        if self.show_controllers:
            for ctrl in self.controller_editors:
                ctrl.on_button_release(widget, event)

        self.parent.autoscroll_req = True

        if self.sel_drag and event.button == cfg.select_button:
            if self.sel_dragged:
                self.sel_drag = False
                self.undo_buff.add_state()
                # cap selection
                if self.select_start:
                    ssx = max(self.select_start[0], 0)
                    sex = max(self.select_end[0], 0)
                    ssy = max(self.select_start[1], 0)
                    sey = max(self.select_end[1], 0)

                    ssx = min(ssx, len(self.trk) - 1)
                    sex = min(sex, len(self.trk) - 1)

                    ssy = min(ssy, self.trk.nrows - 1)
                    sey = min(sey, self.trk.nrows - 1)
                    self.select_start = ssx, ssy
                    self.select_end = sex, sey
            else:
                row = int(event.y / self.txt_height)
                col = int(event.x / self.txt_width)
                self.sel_drag = False
                old = self.select_start[1], self.select_end[1]
                self.select_start = None
                self.select_end = None
                self.edit = col, row
                self.redraw(*(old))
                self.redraw(self.edit[1])
                return True

        if event.button == cfg.select_button:
            self.select = None
            if self.select_start == self.select_end:
                self.select_start = None
                self.select_end = None
                if self.edit:
                    self.redraw(self.edit[1])

            if self.select_start:
                self.edit = None
                # normalise selection
                ssx = self.select_start[0]
                ssy = self.select_start[1]
                sex = self.select_end[0]
                sey = self.select_end[1]

                if sex < ssx:
                    sex, ssx = ssx, sex

                if sey < ssy:
                    sey, ssy = ssy, sey

                self.select_start = ssx, ssy
                self.select_end = sex, sey

            if self.drag:
                self.drag = False
                self.undo_buff.add_state()

        redr = False

        if self.velocity_editor:
            self.velocity_editor = None
            redr = True

        if self.timeshift_editor:
            self.timeshift_editor = None
            redr = True

        if self.prob_editor:
            self.prob_editor = None
            redr = True

        if redr:
            self.configure()
            self.redraw()
            self.parent.prop_view.redraw()
            self.undo_buff.add_state()

        return False

    def on_leave(self, wdg, prm):
        if self.hover:
            oh = self.hover
            self.hover = None
            self.redraw(oh[1])

        if self.keyboard_focus:
            hr = self.keyboard_focus.doodle_hint_row
            self.keyboard_focus.doodle_hint_row = -1
            self.redraw(hr)

    @staticmethod
    def recalc_edit(trk):
        if trk.show_pitchwheel and trk.pitchwheel_editor:
            if trk.pitchwheel_editor.edit > -1:
                trk.edit = (
                    len(trk.trk) if trk.show_notes else 0,
                    trk.pitchwheel_editor.edit,
                )

        if trk.show_controllers:
            for c, wdg in enumerate(trk.controller_editors):
                if wdg.edit > -1:
                    trk.edit = (
                        c
                        + (1 if trk.show_pitchwheel else 0)
                        + (len(trk.trk) if trk.show_notes else 0),
                        wdg.edit,
                    )

    def go_right(self, skip_track=False, rev=False):
        old = self.edit[1]
        inc = 1
        if rev:
            inc *= -1

        self.parent.autoscroll_req = True

        if not skip_track:
            self.edit = self.edit[0] + inc, self.edit[1]

            # are we past last col?
            if self.edit[0] >= (
                (len(self.trk) if self.show_notes else 0)
                + (1 if self.show_pitchwheel else 0)
                + (self.trk.nctrl - 1 if self.show_controllers else 0)
            ):
                self.go_right(True)
                mod.active_track.edit = (
                    0,
                    min(mod.active_track.edit[1], mod.active_track.trk.nrows - 1),
                )
                self.recalc_edit(mod.active_track)
                mod.active_track.redraw()

            # do we wrap over to last col?
            if self.edit and self.edit[0] < 0:
                self.go_left(True)
                mod.active_track.edit = (
                    (
                        (
                            (len(mod.active_track.trk) - 1)
                            if mod.active_track.show_notes
                            else 0
                        )
                        + (1 if mod.active_track.show_pitchwheel else 0)
                        + (
                            mod.active_track.trk.nctrl - 1
                            if mod.active_track.show_controllers
                            else 0
                        )
                    ),
                    min(mod.active_track.edit[1], mod.active_track.trk.nrows - 1),
                )

                e = mod.active_track.edit
                TrackView.leave_all()
                mod.active_track.edit = e
                self.recalc_edit(mod.active_track)
                mod.active_track.redraw()
                mod.active_track.parent.prop_view.redraw()

            if mod.active_track.show_pitchwheel:
                if mod.active_track.edit[0] == (
                    len(mod.active_track.trk) if mod.active_track.show_notes else 0
                ):
                    ed = mod.active_track.edit
                    TrackView.leave_all()
                    mod.active_track.edit = ed
                    mod.active_track.pitchwheel_editor.edit = mod.active_track.edit[1]
                    mod.active_track.keyboard_focus = mod.active_track.pitchwheel_editor
                    self.recalc_edit(mod.active_track)
                    mod.active_track.redraw(mod.active_track.edit[1])
                    mod.active_track.parent.prop_view.redraw()

            if mod.active_track.show_controllers:
                c = mod.active_track.edit[0] - (
                    (len(mod.active_track.trk) if mod.active_track.show_notes else 0)
                    + (1 if mod.active_track.show_pitchwheel else 0)
                )
                c = min(c, mod.active_track.trk.nctrl - 2)
                if c > -1 and mod.active_track.edit:
                    e = mod.active_track.edit
                    TrackView.leave_all()
                    mod.active_track.edit = e
                    mod.active_track.controller_editors[c].edit = mod.active_track.edit[
                        1
                    ]
                    mod.active_track.keyboard_focus = (
                        mod.active_track.controller_editors[c]
                    )
                    self.recalc_edit(mod.active_track)
                    self.parent.prop_view.redraw()
                    mod.active_track.redraw()

            # did we leave controllers?
            if self.edit and self.show_notes and self.edit[0] < len(self.trk):
                e = self.edit
                TrackView.leave_all()
                self.edit = e
                self.keyboard_focus = None
                self.parent.prop_view.redraw(self.trk.index)

            self.redraw(old)
            if self.edit:
                self.redraw(self.edit[1])
            return

        # skipping track
        curr = None
        for i, trk in enumerate(self.seq):
            if trk.index == self.trk.index:
                curr = i

        curr += inc
        if curr >= len(self.seq):
            curr = 0

        if curr < 0:
            curr = len(self.seq) - 1

        trk = self.parent.get_tracks()[curr]

        if trk != self:
            self.pmp.silence()

        old = self.edit
        self.edit = None
        TrackView.leave_all()

        self.keyboard_focus = None
        self.parent.change_active_track(trk)

        self.parent.seq.set_midi_focus(trk.trk.index)
        self.parent.prop_view.redraw()

        trk.edit = (
            (0 if trk.show_notes else len(trk.trk)),
            int(round((old[1] * self.spacing) / trk.spacing)),
        )
        trk.redraw(min(trk.edit[1], trk.trk.nrows - 1))

        self.redraw(old[1])

    # ;)
    def go_left(self, skip_track=False, rev=True):
        self.go_right(skip_track, rev)

    def selection(self):
        if not self.select_start or not self.select_end:
            return None

        ssx = min(self.select_start[0], len(self.trk) - 1)
        ssy = self.select_start[1]
        sex = min(self.select_end[0], len(self.trk) - 1)
        sey = self.select_end[1]

        if sex < ssx:
            sex, ssx = ssx, sex

        if sey < ssy:
            sey, ssy = ssy, sey

        ret = []
        for x in range(ssx, sex + 1):
            for y in range(ssy, sey + 1):
                ret.append(self.trk[x][y])
        return ret

    def to_dict(self, sel_only=False):
        ret = {}
        if sel_only:
            ret = self.copy_selection(dest=ret)
            return ret

        for x in range(len(self.trk)):
            for y in range(self.trk.nrows):
                r = self.trk[x][y]
                ret[(x, y)] = (r.type, r.note, r.velocity, r.delay)

        return ret

    def copy_selection(self, cut=False, dest=None):
        ssx = 0
        ssy = 0
        sex = 0
        sey = 0

        if self.edit:
            ssx = self.edit[0]
            ssy = self.edit[1]
            sex = self.edit[0]
            sey = self.edit[1]

        if self.select_start and self.select_end:
            ssx = min(self.select_start[0], len(self.trk) - 1)
            ssy = self.select_start[1]
            sex = min(self.select_end[0], len(self.trk) - 1)
            sey = self.select_end[1]
        else:
            return None

        # single row - don't copy if empty
        if ssy == sey:
            if self.trk[ssx][ssy].type == 0:
                return None

        if sex < ssx:
            sex, ssx = ssx, sex

        if sey < ssy:
            sey, ssy = ssy, sey

        if dest is None:
            d = TrackView.clipboard
        else:
            d = dest

        d.clear()

        for x in range(ssx, sex + 1):
            for y in range(ssy, sey + 1):
                r = self.trk[x][y]
                d[(x - ssx, y - ssy)] = (
                    r.type,
                    r.note,
                    r.velocity,
                    r.delay,
                    r.prob,
                    r.velocity_range,
                    r.delay_range,
                )

                if cut:
                    self.trk[x][y].clear()

        return d

    def paste(self, repl=False):
        if not TrackView.clipboard:
            return

        ssx = -1

        if self.edit:
            ssx = self.edit[0]

        if self.select_start and self.select_end:
            ssx = min(self.select_start[0], self.select_end[0])
            ssx = min(ssx, self.trk.nrows - 1)

        if ssx < 0:
            return

        d = TrackView.clipboard
        dx = 0
        dy = 0

        for v in d:
            dx = max(dx, v[0])
            dy = max(dy, v[1])

        while len(self.trk) - ssx < (dx + 1):
            self.trk.add_column()

        if self.edit:
            new_y = None
            for k in d:
                dx = self.edit[0] + k[0]
                dy = self.edit[1] + k[1]
                new_y = min(dy + cfg.skip, self.trk.nrows - 1)
                if dy < self.trk.nrows:
                    r = d[k]
                    if r[0]:
                        self.trk[dx][dy].type = r[0]
                        self.trk[dx][dy].note = r[1]
                        self.trk[dx][dy].velocity = r[2]
                        self.trk[dx][dy].delay = r[3]
                        self.trk[dx][dy].prob = r[4]
                        self.trk[dx][dy].velocity_range = r[5]
                        self.trk[dx][dy].delay_range = r[6]
                    elif repl:
                        self.trk[dx][dy].type = 0
                        self.trk[dx][dy].note = 0
                        self.trk[dx][dy].velocity = 0
                        self.trk[dx][dy].delay = 0
                        self.trk[dx][dy].prob = 0
                        self.trk[dx][dy].velocity_range = 0
                        self.trk[dx][dy].delay_range = 0

            if new_y:
                self.edit = self.edit[0], new_y
        else:
            ssx = min(self.select_start[0], len(self.trk) - 1)
            ssy = self.select_start[1]
            sex = min(self.select_end[0], len(self.trk) - 1)
            sey = self.select_end[1]

            if sex < ssx:
                sex, ssx = ssx, sex

            if sey < ssy:
                sey, ssy = ssy, sey

            dd = []
            for y in range(dy + 1):
                row = []
                for x in range(dx + 1):
                    t = (0, 0, 0, 0)
                    row.append(t)

                dd.append(row)

            for k in d:
                r = d[k]
                dd[k[1]][k[0]] = r

            yy = 0
            for y in range(ssy, sey + 1):
                x = ssx  # dx
                for r in dd[yy]:
                    if r[0]:
                        self.trk[x][y].type = r[0]
                        self.trk[x][y].note = r[1]
                        self.trk[x][y].velocity = r[2]
                        self.trk[x][y].delay = r[3]
                        self.trk[x][y].prob = r[4]
                        self.trk[x][y].velocity_range = r[5]
                        self.trk[x][y].delay_range = r[6]
                    elif repl:
                        self.trk[x][y].type = 0
                        self.trk[x][y].note = 0
                        self.trk[x][y].velocity = 0
                        self.trk[x][y].delay = 0
                        self.trk[x][y].prob = 0
                        self.trk[x][y].velocity_range = 0
                        self.trk[x][y].delay_range = 0
                    x += 1

                yy += 1
                if yy >= len(dd):
                    yy = 0

        self.parent.redraw_track(self.trk)

    def midi_in(self, midin):
        m_note = midin["note"]
        m_type = midin["type"]
        m_velocity = midin["velocity"]
        m_channel = midin["channel"]

        if m_type == 1:  # or m_type == 2:
            if (
                self.edit
                and self.edit[0] < len(self.trk)
                and m_note
                and mod.record == 0
            ):
                self.undo_buff.add_state()
                old = self.edit[1]
                self.trk[self.edit[0]][self.edit[1]].type = m_type
                self.trk[self.edit[0]][self.edit[1]].note = m_note
                self.trk[self.edit[0]][self.edit[1]].velocity = m_velocity
                self.trk[self.edit[0]][self.edit[1]].time = 0

                self.edit = self.edit[0], self.edit[1] + cfg.skip
                if self.edit[1] >= self.trk.nrows:
                    self.edit = self.edit[0], self.edit[1] - self.trk.nrows

                while self.edit[1] < 0:
                    self.edit = self.edit[0], self.edit[1] + self.trk.nrows
                self.redraw(self.edit[1])
                self.redraw(old)
                self.undo_buff.add_state()
                return True

        # fix controller edit
        if m_type == 4 and mod.record == 0:
            for c in self.controller_editors:
                if (
                    -1
                    < c.edit
                    < self.trk.nrows
                    # and self.trk.channel == m_channel
                    # and m_note == self.trk.ctrls[c.ctrlnum]
                ):
                    if self.trk.ctrl[c.ctrlnum][c.edit].velocity != m_velocity:
                        if self.trk.ctrl[c.ctrlnum][c.edit].velocity == -1:  # new node
                            c.undo_buff.add_state()
                            empty = True
                            for r in c.env:
                                if int(r["y"]) < c.edit:
                                    empty = False

                            self.trk.ctrl[c.ctrlnum][c.edit].linked = 0 if empty else 1

                        self.trk.ctrl[c.ctrlnum][c.edit].velocity = m_velocity
                        self.trk.ctrl[c.ctrlnum].refresh()
                        c.redraw_env()
                        self.redraw(ctrl=c)
                        self.reblit()

        return False

    def toggle_time(self):
        self.show_timeshift = not self.show_timeshift
        self.parent.redraw_track(self.trk)
        return True

    def toggle_probs(self):
        self.show_probs = not self.show_probs
        self.parent.redraw_track(self.trk)
        return True

    def toggle_pitch(self):
        self.show_pitchwheel = not self.show_pitchwheel

        if not self.show_pitchwheel:
            if self.keyboard_focus == self.pitchwheel_editor:
                ed = self.pitchwheel_editor.edit
                self.pitchwheel_editor.edit = -1

                if self.show_controllers and self.trk.nctrl > 1:
                    self.controller_editors[0].edit = ed
                    self.keyboard_focus = self.controller_editors[0]
                elif self.show_notes:
                    self.keyboard_focus = None
                    if ed > -1:
                        self.edit = len(self.trk) - 1, ed

        self.recalc_edit(self)
        self.parent.redraw_track(self.trk)
        return True

    def toggle_notes(self):
        if self.show_notes:
            if not self.show_controllers or self.trk.nctrl < 2:
                return True

        self.show_notes = not self.show_notes

        # are we editing?
        if self.edit and self.edit[0] < len(self.trk) and self.keyboard_focus is None:
            if self.show_pitchwheel:
                self.pitchwheel_editor.edit = self.edit[1]
                self.keyboard_focus = self.pitchwheel_editor
            elif self.show_controllers and self.trk.nctrl > 1:
                self.keyboard_focus = self.controller_editors[0]
                self.controller_editors[0].edit = self.edit[1]

        if not self.edit and self.keyboard_focus is None:
            if self.show_pitchwheel:
                self.keyboard_focus = self.pitchwheel_editor
            elif self.show_controllers:
                self.keyboard_focus = self.controller_editors[0]

        self.recalc_edit(self)
        self.parent.redraw_track(self.trk)
        self.parent.prop_view.redraw(self.trk)
        return True

    def toggle_controls(self):
        if self.show_controllers:
            if not self.show_notes:
                return True

        self.show_controllers = not self.show_controllers

        r = -1
        # preserve row
        if not self.show_controllers:
            if self.keyboard_focus and self.keyboard_focus != self.pitchwheel_editor:
                r = self.keyboard_focus.edit
                self.keyboard_focus.edit = -1

                if self.show_pitchwheel:
                    self.pitchwheel_editor.edit = r
                    self.keyboard_focus = self.pitchwheel_editor
                else:
                    if r > -1:
                        self.edit = len(self.trk) - 1, r

                    self.keyboard_focus = None

        self.recalc_edit(self)
        self.parent.redraw_track(self.trk)
        return True

    def on_key_press(self, widget, event):
        if not self.trk:
            return False

        shift = False
        ctrl = False
        alt = False

        if event.state:
            if event.state & Gdk.ModifierType.SHIFT_MASK:
                shift = True

            if event.state & Gdk.ModifierType.CONTROL_MASK:
                ctrl = True

            if event.state & Gdk.ModifierType.MOD1_MASK:
                alt = True

        if cfg.key["exit_edit"].matches(event):
            self.leave_all()
            return True

        if self.velocity_editor:
            self.velocity_editor.on_key_press(widget, event)

        if cfg.key["track_resend_patch"].matches(event):
            prg = self.trk.get_program()
            self.trk.send_program_change(prg[2])
            return

        if cfg.key["toggle_notes"].matches(event):
            return self.toggle_notes()

        if cfg.key["toggle_time"].matches(event):
            return self.toggle_time()

        if cfg.key["toggle_pitch"].matches(event):
            return self.toggle_pitch()

        if cfg.key["toggle_controllers"].matches(event):
            return self.toggle_controls()

        if cfg.key["toggle_probs"].matches(event):
            return self.toggle_probs()

        if self.keyboard_focus is not None and self.select_start is None:
            if self.keyboard_focus.on_key_press(widget, event):
                return True

        if cfg.key["track_clear"].matches(event):
            if self.pitchwheel_editor:
                self.pitchwheel_editor.undo_buff.add_state()

            self.undo_buff.add_state()

            self.trk.clear()

            if self.pitchwheel_editor:
                self.pitchwheel_editor.undo_buff.add_state()

            self.undo_buff.add_state()
            self.trk.kill_notes()
            self.redraw_full()
            return True

        if cfg.key["undo"].matches(event):
            self.undo_buff.restore()
            self.optimise()
            self.trk.kill_notes()
            self.redraw()
            self.parent.redraw_track(self.trk)
            return True

        if cfg.key["copy"].matches(event):
            self.copy_selection()
            return True

        if cfg.key["cut"].matches(event):
            self.undo_buff.add_state()
            self.copy_selection(True)
            self.redraw()
            return True

        if cfg.key["paste"].matches(event):
            self.undo_buff.add_state()
            self.paste()
            self.redraw()
            self.undo_buff.add_state()
            self.parent.prop_view.redraw(self.trk.index)
            return True

        if cfg.key["paste_over"].matches(event):
            self.undo_buff.add_state()
            self.paste(True)
            self.redraw()
            self.undo_buff.add_state()
            self.parent.prop_view.redraw(self.trk.index)
            return True

        if cfg.key["select_all"].matches(event):
            if self.edit:  # select current col if in edit
                self.select_start = self.edit[0], 0
                self.select_end = self.edit[0], self.trk.nrows - 1
                self.edit = None
                self.redraw()
            elif self.select_start:
                if (
                    self.select_start[1] == 0
                    and self.select_end[1] == self.trk.nrows - 1
                ):
                    # deselect all
                    if (
                        self.select_start[0] == 0
                        and self.select_end[0] == len(self.trk) - 1
                    ):
                        self.select_start = self.select_end = None
                        self.redraw()
                    else:  # select all
                        self.select_start = 0, 0
                        self.select_end = len(self.trk) - 1, self.trk.nrows - 1
                        self.redraw()

                else:  # select current col
                    self.select_start = self.select_start[0], 0
                    self.select_end = self.select_end[0], self.trk.nrows - 1
                    self.redraw()
            else:  # simply select all
                self.select_start = 0, 0
                self.select_end = len(self.trk) - 1, self.trk.nrows - 1
                self.redraw()

            return True

        if (
            self.edit
            and cfg.key["note_off"].matches(event)
            and self.keyboard_focus is None
        ):
            self.trk[self.edit[0]][self.edit[1]].clear()
            self.trk[self.edit[0]][self.edit[1]].type = 2

            old = self.edit[1]
            self.edit = self.edit[0], self.edit[1] + cfg.skip

            if self.edit[1] >= self.trk.nrows:
                self.edit = self.edit[0], self.edit[1] - self.trk.nrows

            while self.edit[1] < 0:
                self.edit = self.edit[0], self.edit[1] + self.trk.nrows

            self.redraw(self.edit[1])
            self.redraw(old)

            self.undo_buff.add_state()

        note = (
            self.pmp.key2note(Gdk.keyval_to_lower(event.keyval))
            if not ctrl and not alt and not shift
            else -23
        )

        if self.edit and self.edit[0] < len(self.trk) and note >= 0 and mod.record == 0:
            self.undo_buff.add_state()
            old = self.edit[1]
            rw = self.trk[self.edit[0]][self.edit[1]]
            rw.note = note
            rw.velocity = cfg.velocity
            rw.type = 1
            rw.prob = 0

            self.edit = self.edit[0], self.edit[1] + cfg.skip
            if self.edit[1] >= self.trk.nrows:
                self.edit = self.edit[0], self.edit[1] - self.trk.nrows

            while self.edit[1] < 0:
                self.edit = self.edit[0], self.edit[1] + self.trk.nrows
            self.redraw(self.edit[1])
            self.redraw(old)
            self.undo_buff.add_state()
            return True

        redr = False
        old = self.edit

        sel = self.selection()
        if self.edit and self.edit[0] < len(self.trk):
            sel = []
            sel.append(self.trk[self.edit[0]][self.edit[1]])

        if cfg.key["transp_up"].matches(event):
            for r in sel:
                if r.type:
                    r.note = min(r.note + 1, 127)

            self.undo_buff.add_state()
            if self.edit:
                self.redraw(self.edit[1])
            else:
                self.redraw(self.select_start[1], self.select_end[1])
            return True

        if cfg.key["transp_12_up"].matches(event):
            for r in sel:
                if r.type:
                    r.note = min(r.note + 12, 127)

            self.undo_buff.add_state()
            if self.edit:
                self.redraw(self.edit[1])
            else:
                self.redraw(self.select_start[1], self.select_end[1])
            return True

        if cfg.key["transp_down"].matches(event):
            for r in sel:
                if r.type:
                    r.note = max(r.note - 1, 0)

            self.undo_buff.add_state()
            if self.edit:
                self.redraw(self.edit[1])
            else:
                self.redraw(self.select_start[1], self.select_end[1])
            return True

        if cfg.key["transp_12_down"].matches(event):
            for r in sel:
                if r.type:
                    r.note = max(r.note - 12, 0)

            self.undo_buff.add_state()
            if self.edit:
                self.redraw(self.edit[1])
            else:
                self.redraw(self.select_start[1], self.select_end[1])
            return True

        if cfg.key["velocity_up"].matches(event):
            for r in sel:
                if r.type == 1:
                    r.velocity = min(r.velocity + 1, 127)
                    cfg.velocity = r.velocity

            self.undo_buff.add_state()
            if self.edit:
                self.redraw(self.edit[1])
            else:
                self.redraw(self.select_start[1], self.select_end[1])
            return True

        if cfg.key["velocity_10_up"].matches(event):
            for r in sel:
                if r.type == 1:
                    r.velocity = min(r.velocity + 10, 127)
                    cfg.velocity = r.velocity

            self.undo_buff.add_state()
            if self.edit:
                self.redraw(self.edit[1])
            else:
                self.redraw(self.select_start[1], self.select_end[1])
            return True

        if cfg.key["velocity_down"].matches(event):
            for r in sel:
                if r.type == 1:
                    r.velocity = max(r.velocity - 1, 0)
                    cfg.velocity = r.velocity

            self.undo_buff.add_state()
            if self.edit:
                self.redraw(self.edit[1])
            else:
                self.redraw(self.select_start[1], self.select_end[1])
            return True

        if cfg.key["velocity_10_down"].matches(event):
            for r in sel:
                if r.type == 1:
                    r.velocity = max(r.velocity - 10, 0)
                    cfg.velocity = r.velocity

            self.undo_buff.add_state()
            if self.edit:
                self.redraw(self.edit[1])
            else:
                self.redraw(self.select_start[1], self.select_end[1])
            return True

        if event.keyval == 65364:  # down
            self.parent.autoscroll_req = True
            if self.edit:
                if shift:
                    self.select_start = self.edit
                    self.select_end = (
                        self.edit[0],
                        min(self.edit[1] + 1, self.trk.nrows - 1),
                    )
                    self.edit = None
                    self.redraw(self.select_start[1], self.select_end[1])
                    return True

                self.edit = self.edit[0], self.edit[1] + 1
                if self.edit[1] >= self.trk.nrows:
                    self.edit = self.edit[0], 0

                self.redraw(self.edit[1])
                redr = True
            else:
                if shift:
                    oldy = self.select_start[1]
                    oldyy = self.select_end[1]
                    self.select_end = (
                        self.select_end[0],
                        min(self.select_end[1] + 1, self.trk.nrows - 1),
                    )
                    self.redraw(oldy, oldyy)
                    self.redraw(self.select_start[1], self.select_end[1])
                    return True

                if self.select_start:
                    old = self.select_start[1], self.select_end[1]
                    self.edit = (
                        self.select_end[0],
                        min(self.select_end[1] + 1, self.trk.nrows - 1),
                    )
                    self.select_start = None
                    self.select_end = None
                    self.redraw(*(old))
                    self.redraw(self.edit[1])
                return True

        if event.keyval == 65362:  # up
            self.parent.autoscroll_req = True
            if self.edit:
                if shift:
                    self.select_start = self.edit
                    self.select_end = self.edit[0], max(self.edit[1] - 1, 0)
                    self.edit = None
                    self.redraw(self.select_start[1], self.select_end[1])
                    return True

                self.edit = self.edit[0], self.edit[1] - 1
                if self.edit[1] < 0:
                    self.edit = self.edit[0], self.trk.nrows - 1

                self.redraw(self.edit[1])
                redr = True
            else:
                if shift:
                    oldy = self.select_start[1]
                    oldyy = self.select_end[1]
                    self.select_end = self.select_end[0], max(self.select_end[1] - 1, 0)
                    self.redraw(oldy, oldyy)
                    self.redraw(self.select_start[1], self.select_end[1])
                    return True

                if self.select_start:
                    old = self.select_start[1], self.select_end[1]
                    self.edit = self.select_end[0], max(self.select_end[1] - 1, 0)
                    self.select_start = None
                    self.select_end = None
                    self.redraw(*(old))
                    self.redraw(self.edit[1])
                return True

        if event.keyval == 65363:  # right
            self.parent.autoscroll_req = True
            if not shift:
                if self.select_start:
                    old = self.select_start[1], self.select_end[1]
                    self.edit = self.select_end
                    self.select_start = None
                    self.select_end = None
                    self.redraw(*old)

                if self.edit:
                    self.go_right()
                return True

            if shift:
                if self.edit:
                    self.select_start = self.edit
                    self.select_end = (
                        min(self.edit[0] + 1, len(self.trk) - 1),
                        self.edit[1],
                    )
                    self.edit = None
                    self.redraw(self.select_start[1], self.select_end[1])
                    return True

                if self.select_end:
                    self.select_end = (
                        min(self.select_end[0] + 1, len(self.trk) - 1),
                        self.select_end[1],
                    )
                    self.redraw(self.select_start[1], self.select_end[1])
                    return True

        if event.keyval == 65361:  # left
            self.parent.autoscroll_req = True
            if not shift:
                if self.select_start:
                    old = self.select_start[1], self.select_end[1]
                    self.edit = self.select_end
                    self.select_start = None
                    self.select_end = None
                    self.redraw(*(old))

                if self.edit:
                    self.go_left()
                return True

            if shift:
                if self.edit:
                    self.select_start = self.edit
                    self.select_end = max(self.edit[0] - 1, 0), self.edit[1]
                    self.edit = None
                    self.redraw(self.select_start[1], self.select_end[1])
                    return True

                if self.select_end:
                    self.select_end = max(self.select_end[0] - 1, 0), self.select_end[1]
                    self.redraw(self.select_start[1], self.select_end[1])
                    return True

        if event.keyval == 65366:  # page-down
            self.parent.autoscroll_req = True
            if not shift:
                old = None
                if self.edit:
                    old = self.edit[1], self.edit[1]
                    self.edit = self.edit[0], self.edit[1] + 1

                elif self.select_end:
                    old = self.select_start[1], self.select_end[1]
                    self.edit = self.select_end[0], self.select_end[1] + 1
                    self.select_end = None
                    self.select_start = None

                if not self.edit:
                    return True

                while not self.edit[1] % self.parent.highlight == 0:
                    self.edit = self.edit[0], self.edit[1] + 1

                if self.edit[1] >= self.trk.nrows:
                    self.edit = self.edit[0], self.trk.nrows - 1

                if old:
                    self.redraw(*(old))

                self.redraw(self.edit[1])
                return True

            if shift:
                if self.edit:
                    self.select_start = self.edit
                    self.select_end = self.edit[0], self.edit[1]
                    self.edit = None

                if self.select_end:
                    old = self.select_start[1], self.select_end[1]
                    self.select_end = self.select_end[0], self.select_end[1] + 1

                    while not self.select_end[1] % self.parent.highlight == 0:
                        self.select_end = self.select_end[0], self.select_end[1] + 1

                    self.select_end = (
                        self.select_end[0],
                        min(self.select_end[1], self.trk.nrows - 1),
                    )

                    self.redraw(*(old))
                    self.redraw(self.select_start[1], self.select_end[1])
                return True

        if event.keyval == 65365:  # page-up
            self.parent.autoscroll_req = True
            if not shift:
                old = None
                if self.edit:
                    old = self.edit[1], self.edit[1]
                    self.edit = self.edit[0], self.edit[1] - 1

                elif self.select_end:
                    old = self.select_start[1], self.select_end[1]
                    self.edit = self.select_end[0], self.select_end[1] - 1
                    self.select_end = None
                    self.select_start = None

                if not self.edit:
                    return True

                while not self.edit[1] % self.parent.highlight == 0:
                    self.edit = self.edit[0], self.edit[1] - 1

                self.edit = self.edit[0], max(self.edit[1], 0)

                if old:
                    self.redraw(*(old))

                self.redraw(self.edit[1])
                return True

            if shift:
                if self.edit:
                    self.select_start = self.edit
                    self.select_end = self.edit[0], self.edit[1]
                    self.edit = None

                if self.select_end:
                    old = self.select_start[1], self.select_end[1]
                    self.select_end = self.select_end[0], self.select_end[1] - 1

                    while not self.select_end[1] % self.parent.highlight == 0:
                        self.select_end = self.select_end[0], self.select_end[1] - 1

                    self.select_end = self.select_end[0], max(self.select_end[1], 0)
                    self.redraw(*(old))
                    self.redraw(self.select_start[1], self.select_end[1])
                return True

        if event.keyval == 65360:  # home
            self.parent.autoscroll_req = True
            if not shift:
                if self.edit:
                    old = self.edit[1], self.edit[1]

                if self.select_start:
                    old = self.select_start[1], self.select_end[1]
                    self.edit = self.select_end
                    self.select_start = None
                    self.select_end = None

                if self.edit:
                    self.edit = self.edit[0], 0
                    self.redraw(*(old))
                    self.redraw(self.edit[1])
                return True

            if shift:
                if self.edit:
                    self.select_start = self.edit
                    self.select_end = self.edit[0], 0
                    self.edit = None

                if self.select_end:
                    old = self.select_start[1], self.select_end[1]
                    self.select_end = self.select_end[0], 0
                    self.redraw(*(old))
                    self.redraw(self.select_start[1], self.select_end[1])
                return True

        if event.keyval == 65367:  # end
            self.parent.autoscroll_req = True
            if not shift:
                if self.edit:
                    old = self.edit[1], self.edit[1]

                if self.select_start:
                    old = self.select_start[1], self.select_end[1]
                    self.edit = self.select_end
                    self.select_start = None
                    self.select_end = None

                if self.edit:
                    self.edit = self.edit[0], self.trk.nrows - 1
                    self.redraw(*(old))
                    self.redraw(self.edit[1])
                return True

            if shift:
                if self.edit:
                    self.select_start = self.edit
                    self.select_end = self.edit[0], self.trk.nrows - 1
                    self.edit = None

                if self.select_end:
                    old = self.select_start[1], self.select_end[1]
                    self.select_end = self.select_end[0], self.trk.nrows - 1
                    self.redraw(*(old))
                    self.redraw(self.select_start[1], self.select_end[1])
                return True

        if redr and old:
            self.redraw(old[1])
            return True

        if cfg.key["delete"].matches(event):
            sel = self.selection()
            if sel:
                for r in sel:
                    r.clear()

                if (
                    self.select_start[1] == 0
                    and self.select_end[1] == self.trk.nrows - 1
                    and self.select_start[0] == 0
                    and self.select_end[0] == len(self.trk) - 1
                ):
                    self.trk.kill_notes()

                self.undo_buff.add_state()
                self.redraw()
                return True

            if not self.edit:
                return True

            self.trk[self.edit[0]][self.edit[1]].clear()
            self.redraw(self.edit[1])

            old = self.edit[1]
            self.edit = self.edit[0], self.edit[1] + cfg.skip
            if self.edit[1] >= self.trk.nrows:
                self.edit = self.edit[0], self.trk.nrows - 1

            self.trk.kill_notes()
            self.redraw(self.edit[1])
            self.redraw(old)

            self.undo_buff.add_state()
            return True

        if cfg.key["pull"].matches(event):
            if not self.edit:
                return True

            x = self.edit[0]
            y = self.edit[1]

            for y in range(self.edit[1], self.trk.nrows - 1):
                self.trk[x][y].copy(self.trk[x][y + 1])
                self.redraw(y)

            self.trk[x][self.trk.nrows - 1].clear()
            self.redraw(self.trk.nrows - 1)
            self.undo_buff.add_state()
            return True

        if event.keyval == 65056:  # shift-tab
            if not self.edit:
                return True

            self.go_left(True)
            return True

        if event.keyval == 65289:  # tab
            if not self.edit:
                return True

            self.go_right(True)
            return True

        if cfg.key["push"].matches(event):
            if not self.edit:
                return False

            self.undo_buff.add_state()
            x = self.edit[0]
            y = self.edit[1]

            for y in reversed(range(self.edit[1], self.trk.nrows - 1)):
                self.trk[x][y + 1].copy(self.trk[x][y])
                self.redraw(y + 1)

            self.trk[x][y].clear()
            self.redraw(y)
            self.undo_buff.add_state()

        return False

    def on_key_release(self, widget, event):
        if not self.trk:
            return False

        shift = False
        ctrl = False
        alt = False

        if event.state:
            if event.state & Gdk.ModifierType.SHIFT_MASK:
                shift = True

            if event.state & Gdk.ModifierType.CONTROL_MASK:
                ctrl = True

            if event.state & Gdk.ModifierType.MOD1_MASK:
                alt = True

        if self.pitchwheel_editor:
            self.pitchwheel_editor.on_key_release(widget, event)

        for c in self.controller_editors:
            c.on_key_release(widget, event)

        if self.velocity_editor:
            self.velocity_editor.on_key_release(widget, event)

        if cfg.key["toggle_time"].matches(event):
            return True

        if cfg.key["toggle_pitch"].matches(event):
            return True

        if cfg.key["toggle_controllers"].matches(event):
            return True

        if cfg.key["toggle_probs"].matches(event):
            return True

        if ctrl:
            self.nudge_last_y = -1

            if self.nudge_hide_timeshift:
                self.show_timeshift = False
                self.parent.redraw_track(self.trk)
                self.nudge_hide_timeshift = False

            self.undo_buff.add_state()
            return False

        if shift or alt:
            return False

        if self.keyboard_focus is None:
            self.pmp.key2note(Gdk.keyval_to_lower(event.keyval), True)

        return False

    def optimise(self):
        redr = False
        cont = True

        while cont and len(self.trk) > 1:
            c = self.trk[len(self.trk) - 1]
            found = False
            for r in c:
                if r.type != 0:
                    found = True

            cont = False

            if not found:
                self.parent.shrink_track(self.trk)
                redr = True
                cont = True

            if len(self.trk) == 1:
                cont = False

        if redr:
            self.redraw()

    def resetundo(self):
        self.unfo_buff = TrackUndoBuffer(self.trk)

        for ctr in self.controller_editors:
            ctr.undo_buff = ControllerUndoBuffer(self.trk, ctr.ctrlnum)
