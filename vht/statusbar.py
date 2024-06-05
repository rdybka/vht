# statusbar.py - vahatraker
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

from vht.pulsar import Pulsar
from vht.trackview import TrackView
from vht.portconfigpopover import PortConfigPopover
from vht import *
import cairo
from gi.repository import Gdk, Gtk, Gio
import gi

gi.require_version("Gtk", "3.0")


class StatusBar(Gtk.DrawingArea):
    def __init__(self):
        super(StatusBar, self).__init__()

        self.set_events(
            Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.SCROLL_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
            | Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
        )

        self.connect("draw", self.on_draw)
        self.connect("configure-event", self.on_configure)
        self.connect("motion-notify-event", self.on_motion)
        self.connect("scroll-event", self.on_scroll)
        self.connect("leave-notify-event", self.on_leave)
        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.on_button_release)
        self.connect("query-tooltip", self.on_tooltip)

        self._surface = None
        self._context = None
        self.min_char_width = 73

        self.pos = []
        self.active_field = None
        self.last_active_field = None
        self.add_tick_callback(self.tick)
        self.set_has_tooltip(True)
        self.tt_rect = Gdk.Rectangle()
        self.tt_txt = None

        self.pulse = Pulsar(mod[mod.curr_seq].rpb)

        self.control_held = False
        self.shift_held = False

        self.portpopover = None
        self.portpopover_rect = Gdk.Rectangle()
        mod.status_bar = self

    def redraw(self):
        self.queue_resize()
        cr = self._context
        w = self.get_allocated_width()
        h = self.get_allocated_height()

        (x, y, width, height, dx, dy) = cr.text_extents("0" * self.min_char_width)

        self.set_size_request(1, height * 1.5 * cfg.seq_spacing)

        bar_col = cfg.colour
        intensity = 1.0
        if mod.record:
            bar_col = cfg.record_colour
            intensity = self.pulse.intensity(mod[mod.curr_seq].pos)

        gradient = cairo.LinearGradient(0, 0, 0, h)
        gradient.add_color_stop_rgb(
            0, *(col * cfg.intensity_background * intensity for col in bar_col)
        )
        gradient.add_color_stop_rgb(
            0.3, *(col * cfg.intensity_txt * intensity for col in bar_col)
        )
        gradient.add_color_stop_rgb(
            0.7, *(col * cfg.intensity_txt * intensity for col in bar_col)
        )

        gradient.add_color_stop_rgb(
            1.0, *(col * cfg.intensity_background for col in bar_col)
        )

        cr.set_source(gradient)

        cr.rectangle(0, 0, w, h)
        cr.fill()

        trk = mod.active_track

        t = 0
        r = 0
        c = 0
        cs = mod.curr_seq
        seq = mod[cs]

        self.pos = []

        self.pos.append(0)
        xx = 0

        if trk:
            t = trk.trk.index
            if trk.edit:
                c = trk.edit[0]
                r = trk.edit[1]

        if type(cs) is tuple:
            txt = "T%02d:%02d:%02d:%03d" % (cs[1], t, c, r)
        else:
            txt = "S%02d:%02d:%02d:%03d" % (cs, t, c, r)

        h = ((height * 1.5 * cfg.seq_spacing) / 2.0) + (height / 2.0)

        intensity = 1.0 - intensity

        if mod.record:
            cr.set_source_rgb(*(col * intensity for col in cfg.record_colour))
        else:
            cr.set_source_rgb(*(col * 0 for col in cfg.colour))

        (x, y, width, height, dx, dy) = cr.text_extents(txt)
        cr.move_to(self.pos[-1], h)
        cr.show_text(txt)
        xx += dx
        self.pos.append(xx)

        if self.active_field == 1:
            cr.set_source_rgb(
                *(col * cfg.intensity_txt_highlight for col in cfg.star_colour)
            )
        else:
            cr.set_source_rgb(*(col * intensity for col in cfg.record_colour))

        if cfg.octave > 0:
            txt = " oct:%d" % (cfg.octave - 1)
        else:
            txt = " oct:<"

        (x, y, width, height, dx, dy) = cr.text_extents(txt)
        cr.move_to(self.pos[-1], h)
        cr.show_text(txt)
        xx += dx
        self.pos.append(xx)

        if self.active_field == 2:
            cr.set_source_rgb(
                *(col * cfg.intensity_txt_highlight for col in cfg.star_colour)
            )
        else:
            cr.set_source_rgb(*(col * intensity for col in cfg.record_colour))

        txt = " vel:%d" % cfg.velocity
        *_, dx, _ = cr.text_extents(txt)
        cr.move_to(self.pos[-1], h)
        cr.show_text(txt)
        xx += dx
        self.pos.append(xx)

        if self.active_field == 3:
            cr.set_source_rgb(
                *(col * cfg.intensity_txt_highlight for col in cfg.star_colour)
            )
        else:
            cr.set_source_rgb(*(col * intensity for col in cfg.record_colour))

        txt = " skp:%d" % cfg.skip
        *_, dx, _ = cr.text_extents(txt)
        cr.move_to(self.pos[-1], h)
        cr.show_text(txt)
        xx += dx
        self.pos.append(xx)

        if (
            mod.play_mode == 1
            and self.active_field == 4
            and not mod.timeline_view.curr_change
        ):
            self.active_field = -1

        if self.active_field == 4 or mod.timeline_view.curr_change:
            cr.set_source_rgb(
                *(col * cfg.intensity_txt_highlight for col in cfg.star_colour)
            )
        else:
            cr.set_source_rgb(*(col * intensity for col in cfg.record_colour))

        if mod.timeline_view.curr_change:
            txt = " bpm:%6.2f" % mod.timeline_view.curr_change.bpm
        else:
            txt = " bpm:%6.2f" % mod.bpm

        *_, dx, _ = cr.text_extents(txt)
        cr.move_to(self.pos[-1], h)
        cr.show_text(txt)
        xx += dx
        self.pos.append(xx)

        if self.active_field == 5:
            cr.set_source_rgb(
                *(col * cfg.intensity_txt_highlight for col in cfg.star_colour)
            )
        else:
            cr.set_source_rgb(*(col * intensity for col in cfg.record_colour))

        if self.shift_held and self.active_field == 5 and type(seq.index) is not int:
            strp = mod.timeline.strips[seq.index[1]]
            if self.control_held:
                txt = " rpb:%d!%d" % (strp.rpb_start, strp.rpb_end)
            else:
                txt = " rpb:%d!%d" % (strp.rpb_start, strp.rpb_end)
        else:
            txt = " rpb:%d" % seq.rpb

        *_, dx, _ = cr.text_extents(txt)
        cr.move_to(self.pos[-1], h)
        cr.show_text(txt)
        xx += dx
        self.pos.append(xx)

        if self.active_field == 6:
            cr.set_source_rgb(
                *(col * cfg.intensity_txt_highlight for col in cfg.star_colour)
            )
        else:
            cr.set_source_rgb(*(col * intensity for col in cfg.record_colour))

        txt = " prt:%d" % mod.default_midi_out_port
        *_, dx, _ = cr.text_extents(txt)
        cr.move_to(self.pos[-1], h)
        cr.show_text(txt)

        self.portpopover_rect.x = xx
        self.portpopover_rect.y = 0
        self.portpopover_rect.width = dx
        self.portpopover_rect.height = 10

        xx += dx
        self.pos.append(xx)

        if mod.record:
            cr.set_source_rgb(*(col * intensity for col in cfg.record_colour))
        else:
            cr.set_source_rgb(*(col * intensity for col in cfg.colour))

        dx = 0
        if not cfg.timeline_show:
            if self.active_field == 8:
                cr.set_source_rgb(
                    *(col * cfg.intensity_txt_highlight for col in cfg.star_colour)
                )
            else:
                cr.set_source_rgb(*(col * intensity for col in cfg.record_colour))

            txt = "***"
            *_, dx, _ = cr.text_extents(txt)
            self.pos.append(w - dx)
            self.pos.append(w)
            cr.move_to(w - dx, h)
            cr.show_text(txt)
        else:
            r = mod.timeline.pos
            t = mod.timeline.qb2t(r)
            txt = "%.3f %d:%02d:%02d" % (
                r,
                t // 60,
                t % 60,
                (t * 100) % 100,
            )

            *_, dx, _ = cr.text_extents(txt)
            cr.move_to(w - dx, h)
            cr.show_text(txt)

        end_x = w - dx

        if mod.mainwin.fs and mod.mainwin.hb.props.title:
            *_, dx, _ = cr.text_extents(" ")
            cr.set_source_rgba(*(col * intensity for col in cfg.record_colour), 0.666)
            cr.rectangle(0, 0, end_x - dx, h)
            cr.clip()
            cr.move_to(xx + dx, h)
            cr.show_text(mod.mainwin.hb.props.title)
            cr.reset_clip()

        cr.set_source_rgb(*(col * 0 for col in cfg.colour))
        cr.move_to(0, 0)
        cr.line_to(w, 0)
        cr.stroke()

        self.queue_draw()

    def tick(self, wdg, param):
        self.pulse.freq = mod[mod.curr_seq].rpb
        self.redraw()
        return 1

    def on_configure(self, wdg, event):
        if self._surface:
            self._surface.finish()

        w = wdg.get_allocated_width()
        h = wdg.get_allocated_height()

        self.tt_rect.height = h

        self._surface = wdg.get_window().create_similar_surface(
            cairo.CONTENT_COLOR, w, h
        )

        self._context = cairo.Context(self._surface)
        self._context.set_antialias(cairo.ANTIALIAS_NONE)

        self._context.select_font_face(
            cfg.seq_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD
        )

        fs = cfg.status_bar_font_size
        fits = False
        while not fits:
            self._context.set_font_size(fs)
            _, _, width, *_ = self._context.text_extents("X" * self.min_char_width)
            if w > width:
                fits = True
            else:
                fs -= 1

        self._context.set_line_width((fs / 6.0) * cfg.seq_line_width)

        self.redraw()
        if self.portpopover:
            self.portpopover.set_pointing_to(self.portpopover_rect)
        return True

    def on_draw(self, widget, cr):
        cr.set_source_surface(self._surface, 0, 0)
        cr.paint()
        return False

    def on_motion(self, widget, event):
        self.active_field = None

        xx = 0
        af = -1
        for pos in self.pos:
            if event.x > xx and event.x < pos:
                self.active_field = af
                self.tt_rect.x = xx
                self.tt_rect.y = 0
                self.tt_rect.width = pos - xx

            xx = pos
            af += 1

        if self.last_active_field != self.active_field:
            if not self.active_field:
                self.tt_txt = None

            if self.active_field == 1:  # octave
                self.tt_txt = "<big>↑</big> %s\n<big>↓</big> %s" % (
                    cfg.key["octave_up"],
                    cfg.key["octave_down"],
                )

            if self.active_field == 2:  # velocity
                self.tt_txt = (
                    "<big>⇑</big> %s\n<big>↑</big> %s\n<big>↓</big> %s\n<big>⇓</big> %s"
                    % (
                        cfg.key["velocity_10_up"],
                        cfg.key["velocity_up"],
                        cfg.key["velocity_down"],
                        cfg.key["velocity_10_down"],
                    )
                )

            if self.active_field == 3:  # skip
                self.tt_txt = "<big>↑</big> %s\n<big>↓</big> %s" % (
                    cfg.key["skip_up"],
                    cfg.key["skip_down"],
                )

            if self.active_field == 4:  # bpm
                self.tt_txt = (
                    "<big> ⇑</big> %s\n<big> ↑</big> %s\n<big>.↑</big> %s\n<big>.↓</big> %s\n<big> ↓</big> %s\n<big> ⇓</big> %s"
                    % (
                        cfg.key["bpm_10_up"],
                        cfg.key["bpm_up"],
                        cfg.key["bpm_frac_up"],
                        cfg.key["bpm_frac_down"],
                        cfg.key["bpm_down"],
                        cfg.key["bpm_10_down"],
                    )
                )

            if self.active_field == 5:  # rpb
                self.tt_txt = "<big>↑</big> %s\n<big>↓</big> %s" % (
                    cfg.key["rpb_up"],
                    cfg.key["rpb_down"],
                )

            if self.active_field == 6:  # prt
                self.tt_txt = "<big>↑</big> %s\n<big>↓</big> %s" % (
                    cfg.key["def_port_up"],
                    cfg.key["def_port_down"],
                )

            if self.active_field == 8:  # ***
                self.tt_txt = "<big>toggle timeline</big>\n%s" % (
                    cfg.key["toggle_timeline"],
                )

            self.last_active_field = self.active_field

    def on_scroll(self, widget, event):
        if not self.active_field:
            return True

        up = event.direction == Gdk.ScrollDirection.UP
        down = event.direction == Gdk.ScrollDirection.DOWN

        if self.active_field == 1:
            if up:
                cfg.octave = min(cfg.octave + 1, 10)
            if down:
                cfg.octave = max(cfg.octave - 1, 0)

        if self.active_field == 2:
            if up:
                cfg.velocity = min(cfg.velocity + 1, 127)
            if down:
                cfg.velocity = max(cfg.velocity - 1, 0)

        if self.active_field == 3:
            if up:
                cfg.skip = min(cfg.skip + 1, 16)
            if down:
                cfg.skip = max(cfg.skip - 1, -16)

        if self.active_field == 4:
            bpmch = mod

            if mod.timeline_view.curr_change:
                bpmch = mod.timeline_view.curr_change

            if up:
                bpmch.bpm = min(mod.max_bpm, bpmch.bpm + 1)
            if down:
                bpmch.bpm = max(mod.min_bpm, bpmch.bpm - 1)

        if self.active_field == 5:
            if self.shift_held:
                seqid = mod[mod.curr_seq].index
                if type(seqid) is not int:
                    if self.control_held:
                        if up:
                            mod.timeline.strips[seqid[1]].rpb_end += 1
                        if down:
                            mod.timeline.strips[seqid[1]].rpb_end -= 1
                    else:
                        if up:
                            mod.timeline.strips[seqid[1]].rpb_start += 1
                        if down:
                            mod.timeline.strips[seqid[1]].rpb_start -= 1
                return True

            if up:
                org = mod[mod.curr_seq].rpb
                mod[mod.curr_seq].rpb += 1
                if org != mod[mod.curr_seq].rpb:
                    mod.mainwin.sequence_view.highlight = mod[mod.curr_seq].rpb
                    mod.mainwin.sequence_view.redraw_track()
            if down:
                org = mod[mod.curr_seq].rpb
                mod[mod.curr_seq].rpb -= 1
                if org != mod[mod.curr_seq].rpb:
                    mod.mainwin.sequence_view.highlight = mod[mod.curr_seq].rpb
                    mod.mainwin.sequence_view.redraw_track()

            seqid = mod[mod.curr_seq].index
            if type(seqid) is not int:
                mod.timeline.strips[seqid[1]].rpb_start = mod.timeline.strips[
                    seqid[1]
                ].rpb_end = mod[mod.curr_seq].rpb

        if self.active_field == 6:
            if up:
                mod.default_midi_out_port += 1

            if down:
                mod.default_midi_out_port -= 1

            mod.extras["default_out_port"] = mod.default_midi_out_port

        return True

    def on_leave(self, wdg, prm):
        self.control_held = False
        self.shift_held = False
        self.active_field = None

    def on_button_press(self, widget, event):
        if event.button == 1 and self.active_field == 6:
            if not self.portpopover:
                self.portpopover = PortConfigPopover(self)

            self.portpopover.set_pointing_to(self.portpopover_rect)
            self.portpopover.pop()
            return True

        if event.button == 1 and self.active_field == 8:
            mod.mainwin.show_timeline()

        return False

    def on_key_press(self, widget, event):
        if 65507 <= event.keyval <= 65508:  # ctrl
            self.control_held = True

        if 65505 <= event.keyval <= 65506:  # shift
            self.shift_held = True

    def on_key_release(self, widget, event):
        if 65507 <= event.keyval <= 65508:  # ctrl
            self.control_held = False

        if 65505 <= event.keyval <= 65506:  # shift
            self.shift_held = False

    def on_button_release(self, widget, event):
        up = down = middle = False

        if event.button == 1:
            down = True

        if event.button == 3:
            up = True

        if event.button == 2:
            middle = True

        if self.active_field == 1:
            if up:
                cfg.octave = min(cfg.octave + 1, 10)
            if down:
                cfg.octave = max(cfg.octave - 1, 0)

        if self.active_field == 2:
            if up:
                cfg.velocity = min(cfg.velocity + 1, 127)
            if down:
                cfg.velocity = max(cfg.velocity - 1, 0)

        if self.active_field == 3:
            if up:
                cfg.skip = min(cfg.skip + 1, 16)
            if down:
                cfg.skip = max(cfg.skip - 1, -16)

        if self.active_field == 4:
            bpmch = mod

            if mod.timeline_view.curr_change:
                bpmch = mod.timeline_view.curr_change

            if up:
                bpmch.bpm = min(mod.max_bpm, bpmch.bpm + 1)
            if down:
                bpmch.bpm = max(mod.min_bpm, bpmch.bpm - 1)

        if self.active_field == 5:
            if up:
                org = mod[mod.curr_seq].rpb
                mod[mod.curr_seq].rpb += 1
                if org != mod[mod.curr_seq].rpb:
                    mod.mainwin.sequence_view.highlight = mod[mod.curr_seq].rpb
                    mod.mainwin.sequence_view.redraw_track()
            if down:
                org = mod[mod.curr_seq].rpb
                mod[mod.curr_seq].rpb -= 1
                if org != mod[mod.curr_seq].rpb:
                    mod.mainwin.sequence_view.highlight = mod[mod.curr_seq].rpb
                    mod.mainwin.sequence_view.redraw_track()

            if middle:
                for seq in mod:
                    seq.ketchup()

    def on_tooltip(self, wdg, x, y, kbd, tt):
        if not self.active_field:
            return False

        if not self.tt_txt:
            return False

        tt.set_markup(cfg.tooltip_markup % (self.tt_txt))

        tt.set_tip_area(self.tt_rect)
        return True
