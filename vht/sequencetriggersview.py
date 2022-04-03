# sequencetriggersview.py - vahatraker
#
# Copyright (C) 2022 Remigiusz Dybka - remigiusz.dybka@gmail.com
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
from gi.repository import Gtk, Gio, Gdk
import gi

gi.require_version("Gtk", "3.0")


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

        for i, l in enumerate(["mute:", "cue:", "play:"]):
            lbl = Gtk.Button.new_with_label(l)
            lbl.connect("button-press-event", self.on_butt_in, i)
            lbl.connect("button-release-event", self.on_butt_out, i)
            self.attach(lbl, 0, i, 1, 1)

        entry_wc = 20

        # mute
        self.mute_capture_button = Gtk.ToggleButton()
        self.mute_capture_button.set_tooltip_markup(cfg.tooltip_markup % ("capture"))
        icon = Gio.ThemedIcon(name="media-record")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.mute_capture_button.add(image)
        self.mute_capture_button.connect("toggled", self.on_capture_toggled, 0)

        self.attach(self.mute_capture_button, 1, 0, 1, 1)

        self.mute_entry = Gtk.Entry()
        self.mute_entry.props.sensitive = False

        self.mute_entry.set_width_chars(entry_wc)

        self.attach(self.mute_entry, 3, 0, 1, 1)

        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="edit-delete")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.set_tooltip_markup(cfg.tooltip_markup % ("clear"))
        button.connect("clicked", self.on_clear_clicked, 0)
        self.attach(button, 2, 0, 1, 1)

        # cue
        self.cue_capture_button = Gtk.ToggleButton()
        self.cue_capture_button.set_tooltip_markup(cfg.tooltip_markup % ("capture"))
        icon = Gio.ThemedIcon(name="media-record")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.cue_capture_button.add(image)
        self.cue_capture_button.connect("toggled", self.on_capture_toggled, 1)
        self.attach(self.cue_capture_button, 1, 1, 1, 1)

        self.cue_entry = Gtk.Entry()
        self.cue_entry.props.sensitive = False

        self.cue_entry.set_width_chars(entry_wc)
        self.attach(self.cue_entry, 3, 1, 1, 1)

        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="edit-delete")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.set_tooltip_markup(cfg.tooltip_markup % ("clear"))
        button.connect("clicked", self.on_clear_clicked, 1)
        self.attach(button, 2, 1, 1, 1)

        # play
        self.play_capture_button = Gtk.ToggleButton()
        self.play_capture_button.set_tooltip_markup(cfg.tooltip_markup % ("capture"))
        icon = Gio.ThemedIcon(name="media-record")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.play_capture_button.add(image)
        self.play_capture_button.connect("toggled", self.on_capture_toggled, 2)
        self.attach(self.play_capture_button, 1, 2, 1, 1)

        self.play_midi_entry = Gtk.Entry()
        self.play_midi_entry.props.sensitive = False
        self.play_midi_entry.set_width_chars(entry_wc)
        self.attach(self.play_midi_entry, 3, 2, 1, 1)

        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="edit-delete")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.set_tooltip_markup(cfg.tooltip_markup % ("clear"))
        button.connect("clicked", self.on_clear_clicked, 2)
        self.attach(button, 2, 2, 1, 1)

        self.play_mode_cb = Gtk.ComboBoxText()
        for m in ["on/off", "one shot", "hold"]:
            self.play_mode_cb.append_text(m)

        self.play_mode_cb.connect("changed", self.on_play_mode_changed)
        self.play_mode_cb.set_tooltip_markup(cfg.tooltip_markup % ("play mode"))
        self.attach(self.play_mode_cb, 1, 3, 2, 1)

        self.quantise_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 16, 1
        )

        self.quantise_scale.set_tooltip_markup(cfg.tooltip_markup % ("quantise"))
        self.quantise_scale.connect("value-changed", self.on_quantise_changed)
        self.attach(self.quantise_scale, 3, 3, 1, 1)

        self._mmute = Gtk.Label()
        self._mmute.set_text("")
        evb = Gtk.EventBox()
        evb.add(self._mmute)
        evb.connect("button-press-event", self.on_mouse_cfg_clicked, 0)
        self.attach(evb, 4, 0, 1, 1)

        self._mcue = Gtk.Label()
        self._mcue.set_text("")
        evb = Gtk.EventBox()
        evb.add(self._mcue)
        evb.connect("button-press-event", self.on_mouse_cfg_clicked, 1)
        self.attach(evb, 4, 1, 1, 1)

        self._mplay = Gtk.Label()
        self._mplay.set_text("")
        evb = Gtk.EventBox()
        evb.add(self._mplay)
        evb.connect("button-press-event", self.on_mouse_cfg_clicked, 2)
        self.attach(evb, 4, 2, 1, 1)

        self.refreshing = False
        self.refresh()

        # self.attach(mcue, 4, 1, 1, 1)
        # self.attach(mplay, 4, 2, 1, 1)

        self.show_all()

    @staticmethod
    def desc_trigger(trig):
        knob_char = "ctrl"
        note_char = "note"
        desc = ""
        if trig[0] == 1:
            notes = [
                "C-",
                "C#",
                "D-",
                "D#",
                "E-",
                "F-",
                "F#",
                "G-",
                "G#",
                "A-",
                "A#",
                "B-",
            ]
            note = trig[2] % 12
            octave = trig[2] // 12
            strrep = ""
            if octave < 10:
                strrep = notes[note] + str(octave)
            else:
                strrep = notes[note] + "A"

            desc = "ch:%02d %s:%03d [%3s]" % (trig[1], note_char, trig[2], strrep)

        if trig[0] == 4:
            desc = "ch:%02d %s:%03d" % (trig[1], knob_char, trig[2])

        return desc

    def refresh(self):
        if self.seq > -1:
            self.refreshing = True
            self.quantise_scale.set_value(mod[self.seq].trg_quantise)
            self.play_mode_cb.set_active(mod[self.seq].trg_playmode)
            self.mute_entry.props.text = self.desc_trigger(mod[self.seq].get_trig(0))
            self.cue_entry.props.text = self.desc_trigger(mod[self.seq].get_trig(1))
            self.play_midi_entry.props.text = self.desc_trigger(
                mod[self.seq].get_trig(2)
            )

            ms = mod[self.seq].extras["mouse_cfg"]
            l = ["   ", " l ", " m ", " r "]
            ll = ["no button assigned", "", "middle mouse", "right mouse"]
            self._mmute.set_text(l[ms[0]])
            self._mcue.set_text(l[ms[1]])
            self._mplay.set_text(l[ms[2]])

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

    def on_butt_in(self, wdg, sign, i):
        if i == 0:
            mod[self.seq].trigger_mute()

        if i == 1:
            mod[self.seq].trigger_cue()

        if i == 2:
            mod[self.seq].trigger_play_on()

    def on_butt_out(self, wdg, sign, i):
        if i == 2:
            mod[self.seq].trigger_play_off()

    def on_clear_clicked(self, wdg, c):
        mod[self.seq].set_trig(c, 0, 0, 0)
        self.refresh()

    def on_quantise_changed(self, adj):
        if self.refreshing:
            return

        mod[self.seq].trg_quantise = int(adj.get_value())

    def on_play_mode_changed(self, wdg):
        if self.refreshing:
            return

        mod[self.seq].trg_playmode = wdg.get_active()

    def on_capture_toggled(self, wdg, capt):
        if wdg.get_active():
            mod.gui_midi_capture = True
            self.capture = capt
            self.add_tick_callback(self.tick)
            if capt == 0:
                self.cue_capture_button.set_active(False)
                self.play_capture_button.set_active(False)

            if capt == 1:
                self.mute_capture_button.set_active(False)
                self.play_capture_button.set_active(False)

            if capt == 2:
                self.cue_capture_button.set_active(False)
                self.mute_capture_button.set_active(False)
        else:
            if capt == self.capture:
                self.capture = -1
                mod.gui_midi_capture = False

    def tick(self, wdg, param):
        if self.capture == -1:
            self.mute_capture_button.set_active(False)
            self.cue_capture_button.set_active(False)
            self.play_capture_button.set_active(False)
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
