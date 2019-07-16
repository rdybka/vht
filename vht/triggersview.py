# triggersview.py - Valhalla Tracker
#
# Copyright (C) 2019 Remigiusz Dybka - remigiusz.dybka@gmail.com
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
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio

from vht import cfg, mod

class TriggersView(Gtk.Grid):
	def __init__(self, trk, trkview, parent):
		super(TriggersView, self).__init__()

		self.set_orientation(Gtk.Orientation.VERTICAL)

		self.parent = parent
		self.trk = trk
		self.trkview = trkview
		self.capturing = False

		self.set_column_spacing(3)
		self.set_row_spacing(3)
		self.set_column_homogeneous(True)
		self.set_row_homogeneous(True)

		self.attach(Gtk.Label("mute:"), 0, 0, 1, 1)
		self.attach(Gtk.Label("que:"), 0, 1, 1, 1)
		self.attach(Gtk.Label("play:"), 0, 2, 1, 1)

		self.mute_capture_button = Gtk.ToggleButton()
		self.mute_capture_button.set_tooltip_markup(cfg.tooltip_markup % ("capture"))
		icon = Gio.ThemedIcon(name="media-record")
		image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
		self.mute_capture_button.add(image)
		self.mute_capture_button.connect("toggled", self.on_mute_capture_toggled)

		self.attach(self.mute_capture_button, 1, 0, 1, 1)


		self.show_all()

	def on_mute_capture_toggled(self, wdg):
		if wdg.get_active():
			mod.gui_midi_capture = True
			self.capturing = True
			self.add_tick_callback(self.tick)
		else:
			self.capturing = False
			mod.gui_midi_capture = False

	def tick(self, wdg, param):
		if not self.capturing:
			self.capture_button.set_active(False)
			return False

		midin = mod.get_midi_in_event()

		while midin:
			if midin["type"] == 4:
				self.new_ctrl_adj.set_value(midin["note"])
			midin = mod.get_midi_in_event()

		return True
