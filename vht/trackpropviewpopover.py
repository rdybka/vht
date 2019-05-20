# trackpropviewpopover.py - Valhalla Tracker
#
# Copyright (C) 2019 Remigiusz Dybka - remigiusz.dybka@gmail.com
# @schtixfnord
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
from gi.repository import Gdk, Gtk, Gio

from vht import cfg, mod
from vht.controllersview import ControllersView

class TrackPropViewPopover(Gtk.Popover):
	def __init__(self, parent, trk):
		super(TrackPropViewPopover, self).__init__()
		self.set_relative_to(parent)

		self.set_events(Gdk.EventMask.LEAVE_NOTIFY_MASK
			| Gdk.EventMask.ENTER_NOTIFY_MASK)

		self.connect("leave-notify-event", self.on_leave)
		self.connect("enter-notify-event", self.on_enter)

		self.parent = parent
		self.trk = trk
		self.trkview = parent.trkview
		self.grid = Gtk.Grid()
		self.grid.set_column_spacing(3)
		self.grid.set_row_spacing(3)

		self.entered = False

		if trk:
			button = Gtk.Button()
			icon = Gio.ThemedIcon(name="edit-delete")
			image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
			button.add(image)
			button.connect("clicked", self.on_remove_button_clicked)
			button.set_tooltip_markup(cfg.tooltip_markup % (cfg.key["track_del"]))
			self.grid.attach(button, 3, 0, 1, 1)

			button = Gtk.Button()
			icon = Gio.ThemedIcon(name="list-remove")
			image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
			button.add(image)
			button.connect("clicked", self.on_retract_button_clicked)
			button.set_tooltip_markup(cfg.tooltip_markup % (cfg.key["track_shrink"]))
			self.grid.attach(button, 0, 0, 1, 1)

			button = Gtk.Button()
			icon = Gio.ThemedIcon(name="list-add")
			image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
			button.add(image)
			button.connect("clicked", self.on_expand_button_clicked)
			button.set_tooltip_markup(cfg.tooltip_markup % (cfg.key["track_expand"]))
			self.grid.attach(button, 1, 0, 2, 1)

			button = Gtk.Button()
			icon = Gio.ThemedIcon(name="go-previous")
			image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
			button.add(image)
			button.connect("clicked", self.on_move_left_button_clicked)
			button.set_tooltip_markup(cfg.tooltip_markup % (cfg.key["track_move_left"]))
			self.grid.attach(button, 1, 1, 1, 1)

			button = Gtk.Button()
			icon = Gio.ThemedIcon(name="go-next")
			image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
			button.add(image)
			button.connect("clicked", self.on_move_right_button_clicked)
			button.set_tooltip_markup(cfg.tooltip_markup % (cfg.key["track_move_right"]))
			self.grid.attach(button, 2, 1, 1, 1)

			button = Gtk.Button()
			icon = Gio.ThemedIcon(name="go-first")
			image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
			button.add(image)
			button.connect("clicked", self.on_move_first_button_clicked)
			button.set_tooltip_markup(cfg.tooltip_markup % (cfg.key["track_move_first"]))
			self.grid.attach(button, 0, 1, 1, 1)

			button = Gtk.Button()
			icon = Gio.ThemedIcon(name="go-last")
			image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
			button.add(image)
			button.connect("clicked", self.on_move_last_button_clicked)
			button.set_tooltip_markup(cfg.tooltip_markup % (cfg.key["track_move_last"]))
			self.grid.attach(button, 3, 1, 1, 1)

			self.extend_grid = Gtk.Grid()
			self.extend_grid.set_hexpand(True)
			self.extend_grid.set_vexpand(True)

			self.grid.attach(self.extend_grid,4,0,5,6)

			grid = Gtk.Grid()
			grid.set_column_homogeneous(True)
			grid.set_row_homogeneous(True)
			grid.set_column_spacing(2)
			grid.set_row_spacing(2)

			self.show_notes_button = Gtk.ToggleButton("notes")
			self.show_notes_button.set_tooltip_markup(cfg.tooltip_markup % (cfg.key["toggle_notes"]))
			self.show_timeshift_button = Gtk.ToggleButton("time")
			self.show_timeshift_button.set_tooltip_markup(cfg.tooltip_markup % (cfg.key["toggle_time"]))
			self.show_pitchwheel_button = Gtk.ToggleButton("pitch")
			self.show_pitchwheel_button.set_tooltip_markup(cfg.tooltip_markup % (cfg.key["toggle_pitch"]))
			self.show_controllers_button = Gtk.ToggleButton("ctrl")
			self.show_controllers_button.set_tooltip_markup(cfg.tooltip_markup % (cfg.key["toggle_controls"]))

			self.show_notes_button.connect("toggled", self.on_show_notes_toggled)
			self.show_timeshift_button.connect("toggled", self.on_show_timeshift_toggled)
			self.show_pitchwheel_button.connect("toggled", self.on_show_pitchwheel_toggled)
			self.show_controllers_button.connect("toggled", self.on_show_controllers_toggled)

			grid.attach(Gtk.Label("show:"), 0, 0, 1, 1)
			grid.attach(self.show_notes_button, 1, 0, 1, 1)
			grid.attach(self.show_timeshift_button, 2, 0, 1, 1)
			grid.attach(self.show_pitchwheel_button, 3, 0, 1, 1)
			grid.attach(self.show_controllers_button, 4, 0, 1, 1)

			#self.loop_button = Gtk.CheckButton("loop")
			#grid.attach(self.loop_button, 4, 4, 1, 1)
			grid.attach(Gtk.Label(""), 0, 2, 1, 1)

			self.clone_button = Gtk.Button("clone")
			self.clone_button.set_tooltip_markup(cfg.tooltip_markup % (cfg.key["track_clone"]))
			self.clone_button.connect("clicked", self.on_clone_button_clicked)
			grid.attach(self.clone_button, 4, 3, 1, 1)

			self.name_entry = Gtk.Entry()
			self.name_entry.connect("changed", self.on_name_changed)

			self.name_entry.set_text(self.trk.name)
			self.name_entry.set_activates_default(False)

			grid.attach(self.name_entry, 1, 4, 4, 1)
			grid.attach(Gtk.Label("name:"), 0, 4, 1, 1)

			self.extend_track_grid = grid

			self.extend_controllers_grid = Gtk.Grid()
			grid = self.extend_controllers_grid

			grid.set_column_homogeneous(True)
			grid.set_row_homogeneous(True)
			grid.set_column_spacing(2)
			grid.set_row_spacing(2)

			self.ctrlsview = ControllersView(self.trk, self.trkview, self)

			self.extend_triggers_grid = Gtk.Grid()

			self.extend_notebook = Gtk.Notebook()
			self.extend_notebook.set_hexpand(True)
			self.extend_notebook.set_vexpand(True)

			self.extend_notebook.append_page(self.extend_track_grid, Gtk.Label("track"))
			self.extend_notebook.append_page(self.ctrlsview, Gtk.Label("controllers"))
			self.extend_notebook.append_page(self.extend_triggers_grid, Gtk.Label("triggers"))

			self.extend_grid.attach(self.extend_notebook, 0, 0, 5, 5)
			self.extend_grid.show()

			self.port_adj = Gtk.Adjustment(0, 0, 15, 1.0, 1.0)
			self.port_button = Gtk.SpinButton()
			self.port_button.set_adjustment(self.port_adj)
			self.port_adj.set_value(trk.port)
			self.port_adj.connect("value-changed", self.on_port_changed)

			lbl = Gtk.Label("port:")
			lbl.set_xalign(1.0)

			self.grid.attach(lbl, 0, 2, 1, 1)
			self.grid.attach(self.port_button, 1, 2, 2, 1)

			self.channel_adj = Gtk.Adjustment(1, 1, 16, 1.0, 1.0)
			self.channel_button = Gtk.SpinButton()
			self.channel_button.set_adjustment(self.channel_adj)
			self.channel_adj.set_value(trk.channel)
			self.channel_adj.connect("value-changed", self.on_channel_changed)

			lbl = Gtk.Label("channel:")
			lbl.set_xalign(1.0)

			self.grid.attach(lbl, 0, 3, 1, 1)
			self.grid.attach(self.channel_button, 1, 3, 2, 1)

			self.nsrows_adj = Gtk.Adjustment(1, 1, self.parent.seq.length, 1.0, 1.0)
			self.nsrows_button = Gtk.SpinButton()
			self.nsrows_button.set_adjustment(self.nsrows_adj)
			self.nsrows_adj.set_value(trk.nsrows)
			self.nsrows_adj.connect("value-changed", self.on_nsrows_changed)

			lbl = Gtk.Label("rows:")
			lbl.set_xalign(1.0)

			self.nsrows_check_button = Gtk.CheckButton()
			self.nsrows_check_button.connect("toggled", self.on_nsrows_toggled)

			self.grid.attach(lbl, 0, 4, 1, 1)
			self.grid.attach(self.nsrows_button, 1, 4, 2, 1)
			self.grid.attach(self.nsrows_check_button, 3, 4, 1, 1)

			self.nrows_adj = Gtk.Adjustment(1, 1, 256, 1.0, 1.0)
			self.nrows_button = Gtk.SpinButton()
			self.nrows_button.set_adjustment(self.nrows_adj)
			self.nrows_adj.set_value(trk.nsrows)
			self.nrows_adj.connect("value-changed", self.on_nrows_changed)

			lbl = Gtk.Label("funk:")
			lbl.set_xalign(1.0)

			self.nrows_check_button = Gtk.CheckButton()
			self.nrows_check_button.connect("toggled", self.on_nrows_toggled)

			self.grid.attach(lbl, 0, 5, 1, 1)
			self.grid.attach(self.nrows_button, 1, 5, 2, 1)
			self.grid.attach(self.nrows_check_button, 3, 5, 1, 1)

			self.nrows_button.set_sensitive(False)
			self.nsrows_button.set_sensitive(False)
			self.nrows_check_button.set_sensitive(False)

			self.grid.show_all()
			self.add(self.grid)

			self.extend_notebook.set_current_page(0)
			self.set_modal(False)

	def refresh(self):
		if self.trkview.trk.nctrl == 1:
			self.show_controllers_button.set_sensitive(False)
			self.trkview.show_controllers = False
		else:
			self.show_controllers_button.set_sensitive(True)

		self.show_notes_button.set_active(self.trkview.show_notes)
		self.show_timeshift_button.set_active(self.trkview.show_timeshift)
		self.show_pitchwheel_button.set_active(self.trkview.show_pitchwheel)
		self.show_controllers_button.set_active(self.trkview.show_controllers)

		if not self.trkview.show_notes:
			self.show_controllers_button.set_sensitive(False)

		if not self.show_controllers_button.get_active():
			self.show_notes_button.set_sensitive(False)
		else:
			self.show_notes_button.set_sensitive(True)

	def pop(self):
		mod.clear_popups(self)
		self.channel_adj.set_value(self.trk.channel)
		self.port_adj.set_value(self.trk.port)
		self.nsrows_adj.set_upper(self.parent.seq.length)
		self.nsrows_adj.set_value(self.trk.nsrows)
		self.nrows_adj.set_value(self.trk.nrows)
		self.port_adj.set_upper(mod.nports - 1)

		#self.loop_button.set_active(self.trk.loop) // not yet implemented in vhtlib
		#self.show_notes_button.set_sensitive(False)
		self.refresh()
		self.ctrlsview.rebuild()
		self.popup()
		self.entered = False

	def on_leave(self, wdg, prm):
		if not self.entered:
			return True

		if prm.window == self.get_window():
			if prm.detail != Gdk.NotifyType.INFERIOR:
				self.unpop()
				return True

		return True

	def on_enter(self, wdg, prm):
		if prm.window == self.get_window():
			if prm.detail == Gdk.NotifyType.INFERIOR:
				self.entered = True

		return True

	def unpop(self):
		self.popdown()
		self.parent.button_highlight = False
		self.ctrlsview.capturing = False
		self.parent.popped = False
		self.parent.redraw()

	def on_show_notes_toggled(self, wdg):
		if self.trkview.show_notes != wdg.get_active():
			self.trkview.toggle_notes()

		if wdg.get_active():
			self.show_controllers_button.set_sensitive(True)
		else:
			self.show_controllers_button.set_active(True)
			self.show_controllers_button.set_sensitive(False)

	def on_name_changed(self, wdg):
		self.trk.name = wdg.get_text()
		self.parent.redraw()

	def on_show_timeshift_toggled(self, wdg):
		self.trkview.show_timeshift = wdg.get_active()
		if self.parent.popped:
			self.trkview.redraw_full()
			self.parent.redraw()

	def on_show_pitchwheel_toggled(self, wdg):
		if self.trkview.show_pitchwheel != wdg.get_active():
			self.trkview.toggle_pitch()

		if self.parent.popped:
			self.trkview.redraw_full()
			self.parent.redraw()

	def on_show_controllers_toggled(self, wdg):
		if wdg.get_active():
			if self.trk.nctrl > 1:
				self.show_notes_button.set_sensitive(True)
		else:
			self.show_notes_button.set_active(True)
			self.show_notes_button.set_sensitive(False)

		if self.trkview.show_controllers != wdg.get_active():
			self.trkview.toggle_controls()

		if self.entered:
			self.trkview.redraw_full()
			self.parent.redraw()

	def on_remove_button_clicked(self, switch):
		self.parent.del_track()

	def on_retract_button_clicked(self, switch):
		self.parent.seqview.shrink_track(self.trk)

	def on_expand_button_clicked(self, switch):
		self.parent.seqview.expand_track(self.trk)

	def on_clone_button_clicked(self, wdg):
		self.parent.clone_track(self.trkview)

	def on_port_changed(self, adj):
		self.trk.port = int(adj.get_value())
		self.parent.redraw()

	def on_channel_changed(self, adj):
		self.trk.channel = int(adj.get_value())
		self.parent.redraw()

	def on_nrows_changed(self, adj):
		self.trk.nrows = int(adj.get_value())
		self.parent.seqview.recalculate_row_spacing()

	def on_nsrows_changed(self, adj):
		self.trk.nsrows = int(adj.get_value())

		if not self.nrows_check_button.get_active():
			self.trk.nrows = int(adj.get_value())
			self.nrows_adj.set_value(adj.get_value())

		self.parent.seqview.recalculate_row_spacing()

	def on_nrows_toggled(self, wdg):
		if wdg.get_active():
			self.nrows_button.set_sensitive(True)
			self.nsrows_check_button.set_sensitive(True)
		else:
			self.nrows_button.set_sensitive(False)
			self.nrows_check_button.set_active(False)
			self.nrows_adj.set_value(self.nsrows_adj.get_value())

	def on_nsrows_toggled(self, wdg):
		if wdg.get_active():
			self.nsrows_button.set_sensitive(True)
			self.nrows_check_button.set_sensitive(True)
		else:
			self.nsrows_button.set_sensitive(False)
			self.nrows_button.set_sensitive(False)
			self.nrows_check_button.set_active(False)
			self.nrows_check_button.set_sensitive(False)

			self.nrows_adj.set_value(self.parent.seq.length)
			self.nsrows_adj.set_value(self.parent.seq.length)

	def on_move_left_button_clicked(self, switch):
		self.parent.move_left()

	def on_move_right_button_clicked(self, switch):
		self.parent.move_right()

	def on_move_first_button_clicked(self, switch):
		self.parent.move_first()

	def on_move_last_button_clicked(self, switch):
		self.parent.move_last()


