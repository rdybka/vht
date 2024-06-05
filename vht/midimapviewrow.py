# midimapviewrow.py - vahatraker
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
from gi.repository import Gtk, Gio

from vht.capturebutton import CaptureButton


class MidiMapViewRow(Gtk.ActionBar):
    def __init__(self, parent, desc, mi):
        super(MidiMapViewRow, self).__init__()
        self.parent = parent
        self.cfg = parent.cfg
        self.mod = parent.mod
        self.desc = desc

        self.cm = Gtk.ComboBoxText()
        self.cm.set_hexpand(True)
        self.pack_start(self.cm)

        self.butt_cap = CaptureButton(self.on_capture_toggled, self.on_capture_reset, 4)
        self.pack_end(self.butt_cap)

        self.forbidden = []

        self.mi = mi
        self.refresh()
        self.cm.connect("changed", self.on_combo_changed)
        self.cm_freeze = False

    def on_combo_changed(self, cmb):
        if self.cm_freeze:
            return

        itm = cmb.get_active_text()
        if not self.desc:  # set from none
            self.desc = itm
            self.cfg.midi_in[self.desc] = self.mi
            self.parent.refresh_forbiddens()
            return

        if itm == "none":  # remove entry
            del self.cfg.midi_in[self.desc]
            self.desc = None
            self.parent.refresh_forbiddens()
            return

        del self.cfg.midi_in[self.desc]
        self.desc = itm
        self.cfg.midi_in[self.desc] = self.mi
        self.parent.refresh_forbiddens()

    def describe_trigger(self):
        if self.mi and sum(self.mi):
            return "%02d:%03d" % (self.mi[0], self.mi[2])

        return None

    def refresh(self):
        self.cm_freeze = True
        self.cm.remove_all()

        itms = ["none"]

        for k in self.cfg.mappable_keys:
            if not k in self.forbidden:
                itms.append(k)

        if self.desc and self.desc not in self.cfg.mappable_keys:
            itms.append(self.desc)

        for i in itms:
            self.cm.append_text(i)

        if self.desc:
            self.cm.set_active(itms.index(self.desc))
        else:
            self.cm.set_active(0)

        desc = "capture"
        d2 = self.describe_trigger()
        if d2:
            desc += "\n\n" + d2

        self.butt_cap.set_text(self.describe_trigger())
        # self.butt_cap.set_tooltip_markup(self.cfg.tooltip_markup % (desc))
        self.cm_freeze = False

    def on_capture_reset(self, wdg, c):
        self.mi = None
        self.cfg.midi_in[self.desc] = (0, 0, 0)
        self.refresh()

    def on_capture_toggled(self, wdg, c):
        if wdg.get_active():
            for r in self.parent.box.get_children():
                if r is not self:
                    if r.butt_cap.get_active():
                        r.butt_cap.set_active(False)
                        r.capturing = False

            self.mod.gui_midi_capture = True
            self.capturing = True
            self.add_tick_callback(self.tick)
        else:
            self.capturing = False
            self.mod.gui_midi_capture = False

    def tick(self, wdg, param):
        if not self.capturing:
            return False

        midin = self.mod.get_midi_in_event()

        while midin:
            if midin["type"] == 4 and midin["velocity"] > 0:
                self.mi = (midin["channel"], midin["type"], midin["note"])
                self.cfg.midi_in[self.desc] = self.mi
                self.refresh()

            midin = self.mod.get_midi_in_event()

        return True
