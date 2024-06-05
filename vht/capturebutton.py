# capturebutton.py - vahatraker
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


class CaptureButton(Gtk.ToggleButton):
    def __init__(self, toggled, reset, butt_id=None, min_chars=8):
        super(CaptureButton, self).__init__()
        self.reset = reset
        icon = Gio.ThemedIcon(name="media-record")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.label = Gtk.Label()
        self.label.set_width_chars(min_chars)

        box = Gtk.Box()
        box.pack_start(image, True, False, 0)
        box.pack_end(self.label, True, True, 0)

        self.add(box)
        self.connect("toggled", toggled, butt_id)
        self.connect("button-press-event", self.butt_in, butt_id)

    def set_text(self, txt):
        self.label.set_text(txt if txt else "")

    def butt_in(self, wdg, state, butt_id):
        if state.button == cfg.delete_button:
            self.reset(self, butt_id)
