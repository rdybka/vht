# midimapview.py - vahatraker
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

from vht.midimapviewrow import MidiMapViewRow


class MidiMapView(Gtk.ScrolledWindow):
    def __init__(self, parent):
        super(MidiMapView, self).__init__()
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.parent = parent
        self.mod = parent.mod
        self.cfg = parent.cfg

        self.capturing = False
        self.box = Gtk.Box()
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.box.set_orientation(Gtk.Orientation.VERTICAL)
        self.box.set_homogeneous(False)
        self.box.set_spacing(2)
        self.add(self.box)
        self.rebuild()

    def refresh_forbiddens(self):
        add_empty = False

        chld = self.box.get_children()
        if not chld:
            add_empty = True
        else:
            add_empty = True
            for r in self.box.get_children():
                if not r.desc:
                    add_empty = False

        if add_empty:
            self.box.add(MidiMapViewRow(self, None, None))

        for r in self.box.get_children():
            r.forbidden = []
            for rr in self.box.get_children():
                if r is not rr:
                    if rr.desc:
                        r.forbidden.append(rr.desc)

        for w in self.box.get_children():
            w.refresh()

        self.show_all()

    def rebuild(self, just_gui=False):
        for ch in self.box.get_children():
            ch.destroy()

        for desc, mi in self.cfg.midi_in.items():
            self.box.add(MidiMapViewRow(self, desc, mi))

        self.refresh_forbiddens()
