# sequencetriggersview.py - vahatraker
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

import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, Gio, Gdk
from vht import cfg, mod
from vht.capturebutton import CaptureButton


class SequenceTriggersView(Gtk.Grid):
    def __init__(self, seq, parent):
        super(SequenceTriggersView, self).__init__()

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.parent = parent
        self.seq = seq
        self.capture = -1
        self.butt_handler = None

        self.set_column_spacing(3)
        self.set_row_spacing(3)
        self.set_column_homogeneous(False)
        self.set_row_homogeneous(False)

        self.trig_butts = []

        for i, l in enumerate(["mute", "cue", "play"]):
            lbl = Gtk.Button.new_with_label(l)
            lbl.add_events(
                Gdk.EventMask.LEAVE_NOTIFY_MASK
                | Gdk.EventMask.ENTER_NOTIFY_MASK
                | Gdk.EventMask.BUTTON_PRESS_MASK
                | Gdk.EventMask.SCROLL_MASK
                | Gdk.EventMask.KEY_PRESS_MASK
            )

            lbl.connect("button-press-event", self.on_butt_in, i)
            lbl.connect("button-release-event", self.on_butt_out, i)
            self.trig_butts.append(lbl)
            self.attach(lbl, 0, i, 1, 1)

        entry_wc = 20

        grpent = ["none"]
        for m in range(1, mod.max_trg_grp):
            grpent.append("%2d" % m)

        # mute
        self.mute_capture_button = CaptureButton(
            self.on_capture_toggled, self.on_capture_reset, 0
        )
        self.attach(self.mute_capture_button, 2, 0, 1, 1)

        self.mute_capture_button2 = CaptureButton(
            self.on_capture_toggled, self.on_capture_reset, 3
        )
        self.attach(self.mute_capture_button2, 1, 0, 1, 1)

        self.mute_grp_cb = Gtk.ComboBoxText()
        for e in grpent:
            self.mute_grp_cb.append_text(e)

        self.mute_grp_cb.connect("changed", self.on_grp_changed, 0)
        self.attach(Gtk.Label("grp"), 3, 0, 1, 1)
        self.attach(self.mute_grp_cb, 4, 0, 1, 1)

        # cue
        self.cue_capture_button = CaptureButton(
            self.on_capture_toggled, self.on_capture_reset, 1
        )
        self.cue_capture_button2 = CaptureButton(
            self.on_capture_toggled, self.on_capture_reset, 4
        )
        self.attach(self.cue_capture_button, 2, 1, 1, 1)
        self.attach(self.cue_capture_button2, 1, 1, 1, 1)

        self.cue_grp_cb = Gtk.ComboBoxText()
        for e in grpent:
            self.cue_grp_cb.append_text(e)

        self.cue_grp_cb.connect("changed", self.on_grp_changed, 1)
        self.attach(Gtk.Label("grp"), 3, 1, 1, 1)
        self.attach(self.cue_grp_cb, 4, 1, 1, 1)

        # play
        self.play_capture_button = CaptureButton(
            self.on_capture_toggled, self.on_capture_reset, 2
        )
        self.attach(self.play_capture_button, 2, 2, 1, 1)

        self.play_mode_cb = Gtk.ComboBoxText()
        for m in ["on/off", "one shot", "hold"]:
            self.play_mode_cb.append_text(m)

        self.play_mode_cb.connect("changed", self.on_play_mode_changed)
        self.play_mode_cb.set_tooltip_markup(cfg.tooltip_markup % ("play mode"))
        self.attach(self.play_mode_cb, 1, 2, 1, 1)

        self.quantise_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 16, 1
        )

        self.quantise_scale.connect("value-changed", self.on_quantise_changed)
        self.attach(Gtk.Label("qnt"), 3, 2, 1, 1)
        self.attach(self.quantise_scale, 4, 2, 1, 1)

        self._mmute = Gtk.Label()
        self._mmute.set_text("")
        self._mmute.set_width_chars(3)
        evb = Gtk.EventBox()
        evb.add(self._mmute)
        evb.connect("button-press-event", self.on_mouse_cfg_clicked, 0)
        self.attach(evb, 5, 0, 1, 1)

        self._mcue = Gtk.Label()
        self._mcue.set_text("")
        self._mmute.set_width_chars(3)
        evb = Gtk.EventBox()
        evb.add(self._mcue)
        evb.connect("button-press-event", self.on_mouse_cfg_clicked, 1)
        self.attach(evb, 5, 1, 1, 1)

        self._mplay = Gtk.Label()
        self._mplay.set_text("")
        self._mmute.set_width_chars(3)
        evb = Gtk.EventBox()
        evb.add(self._mplay)
        evb.connect("button-press-event", self.on_mouse_cfg_clicked, 2)
        self.attach(evb, 5, 2, 1, 1)

        self.refreshing = False
        self.refresh()

        self.butts = [
            self.mute_capture_button,
            self.cue_capture_button,
            self.play_capture_button,
            self.mute_capture_button2,
            self.cue_capture_button2,
        ]

        self.show_all()

    @staticmethod
    def desc_trigger(trig):
        empty = ""

        knob_char = "ctrl"
        note_char = "note"
        desc = None
        if trig[0] == 1:
            notes = [
                "c-",
                "c#",
                "d-",
                "d#",
                "e-",
                "f-",
                "f#",
                "g-",
                "g#",
                "a-",
                "a#",
                "b-",
            ]
            note = trig[2] % 12
            octave = (trig[2] // 12) - 1
            strrep = ""
            if octave < 0:
                strrep = notes[note] + "<"
            elif octave < 10:
                strrep = notes[note] + str(octave)
            else:
                strrep = notes[note] + "A"

            # desc = "ch:%02d %s:%03d [%3s]" % (trig[1], note_char, trig[2], strrep)
            desc = "n%02d:%3s" % (trig[1], strrep)

        if trig[0] == 4:
            desc = "c%02d:%03d" % (trig[1], trig[2])

        return desc if desc else empty

    def refresh(self):
        if self.seq > -1:
            self.refreshing = True
            self.quantise_scale.set_value(mod[self.seq].trg_quantise)
            self.play_mode_cb.set_active(mod[self.seq].trg_playmode)
            self.mute_grp_cb.set_active(mod[self.seq].get_trig_grp(0))
            self.cue_grp_cb.set_active(mod[self.seq].get_trig_grp(1))

            self.mute_capture_button.label.set_text(
                self.desc_trigger(mod[self.seq].get_trig(0))
            )

            self.mute_capture_button2.label.set_text(
                self.desc_trigger(mod[self.seq].get_trig(3))
            )

            self.cue_capture_button.label.set_text(
                self.desc_trigger(mod[self.seq].get_trig(1))
            )

            self.cue_capture_button2.label.set_text(
                self.desc_trigger(mod[self.seq].get_trig(4))
            )

            self.play_capture_button.label.set_text(
                self.desc_trigger(mod[self.seq].get_trig(2))
            )

            ttips = [
                "click to trigger",
                "click      forward\nctrl-click    back",
            ]

            if mod[self.seq].get_trig_grp(0):
                self.trig_butts[0].set_tooltip_markup(cfg.tooltip_markup % (ttips[1]))
                self.mute_capture_button2.set_sensitive(True)
            else:
                self.mute_capture_button2.set_sensitive(False)
                self.trig_butts[0].set_tooltip_markup(cfg.tooltip_markup % (ttips[0]))

            if mod[self.seq].get_trig_grp(1):
                self.cue_capture_button2.set_sensitive(True)
                self.trig_butts[1].set_tooltip_markup(cfg.tooltip_markup % (ttips[1]))
            else:
                self.cue_capture_button2.set_sensitive(False)
                self.trig_butts[1].set_tooltip_markup(cfg.tooltip_markup % (ttips[0]))

            self.trig_butts[2].set_tooltip_markup(cfg.tooltip_markup % (ttips[0]))

            # self.mute_entry.props.text = self.desc_trigger(mod[self.seq].get_trig(0))
            # self.cue_entry.props.text = self.desc_trigger(mod[self.seq].get_trig(1))
            # self.play_midi_entry.props.text = self.desc_trigger(
            #    mod[self.seq].get_trig(2)
            # )

            ms = mod[self.seq].extras["mouse_cfg"]
            l = ["   ", " l ", " m ", " r "]
            ll = ["no button assigned", "", "middle mouse", "right mouse"]
            self._mmute.set_text(l[ms[0]])
            self._mcue.set_text(l[ms[1]])
            self._mplay.set_text(l[ms[2]])

            if self.capture == -1:
                for b in self.butts:
                    b.set_active(False)

            self.refreshing = False

    def on_mouse_cfg_clicked(self, wdg, evt, d):
        if evt.button < 2:
            return
        x = mod[self.seq].extras
        ms = x["mouse_cfg"]

        for b in range(len(ms)):
            if ms[b] == evt.button:
                ms[b] = 0

        ms[d] = evt.button
        x["mouse_cfg"] = ms
        self.refresh()
        mod.should_save = True

    def on_butt_in(self, wdg, sign, i):
        if sign.get_click_count()[1] > 1:
            return

        ctrl = sign.state & Gdk.ModifierType.CONTROL_MASK

        if i == 0:
            if not ctrl:
                mod[self.seq].trigger_mute_forward()
            else:
                mod[self.seq].trigger_mute_back()

        if i == 1:
            if not ctrl:
                mod[self.seq].trigger_cue_forward()
            else:
                mod[self.seq].trigger_cue_back()

        if i == 2:
            mod[self.seq].trigger_play_on()

    def on_butt_out(self, wdg, sign, i):
        if i == 2:
            mod[self.seq].trigger_play_off()

    def on_quantise_changed(self, adj):
        if self.refreshing:
            return

        mod[self.seq].trg_quantise = int(adj.get_value())

    def on_play_mode_changed(self, wdg):
        if self.refreshing:
            return

        mod[self.seq].trg_playmode = wdg.get_active()

    def on_grp_changed(self, wdg, tp):
        if self.refreshing:
            return

        act = wdg.get_active()

        mod[self.seq].set_trig_grp(tp, act)
        if act == 0 and tp == 0 and self.capture == 3:
            mod.gui_midi_capture = False
            self.capture = -1

        if act == 0 and tp == 1 and self.capture == 4:
            mod.gui_midi_capture = False
            self.capture = -1

        self.refresh()

    def on_capture_reset(self, wdg, c):
        mod[self.seq].set_trig(c, 0, 0, 0)
        self.refresh()

    def on_capture_toggled(self, wdg, capt):
        if wdg.get_active():
            mod.gui_midi_capture = True
            self.capture = capt
            self.add_tick_callback(self.tick)

            for c, b in enumerate(self.butts):
                if capt != c:
                    b.set_active(False)
        else:
            if capt == self.capture:
                self.capture = -1

                for b in self.butts:
                    b.set_active(False)

                mod.gui_midi_capture = False

    def tick(self, wdg, param):
        if self.capture == -1:
            return False

        midin = mod.get_midi_in_event()

        while midin:
            if midin["type"] in [1, 4]:
                if self.capture > -1:
                    mod[self.seq].set_trig(
                        self.capture, midin["type"], midin["channel"], midin["note"]
                    )
                    self.refresh()

            midin = mod.get_midi_in_event()

        return True

        if self._trgview.capture > -1:
            mnt = self.pmp.k2n(event.keyval)
            if mnt > -1:
                mod[self._trgview.seq].set_trig(self._trgview.capture, 1, 1, mnt)
                self._trgview.refresh()
