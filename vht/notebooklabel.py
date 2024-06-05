# notebooklabel.py - vahatraker
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

from vht import cfg, mod
from gi.repository import Gtk, Gdk
import gi

gi.require_version("Gtk", "3.0")


class NotebookLabel(Gtk.EventBox):
    def __init__(self, name, nb, pos):
        super(NotebookLabel, self).__init__()

        self.pos = pos
        self.nb = nb

        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK)

        self.add(Gtk.Label(name))

        self.connect("motion-notify-event", self.motion)
        self.show_all()

    def motion(self, wdg, evt):
        if cfg.notebook_mouseover:
            self.nb.set_current_page(self.pos)
