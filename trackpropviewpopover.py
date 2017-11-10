import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gdk, Gtk, Gio
import cairo

from trackview import TrackView

class TrackPropViewPopover(Gtk.Popover):
	def __init__(self, parent, trk):
		super(TrackPropViewPopover, self).__init__()
		self.set_relative_to(parent)

		self.set_events(Gdk.EventMask.LEAVE_NOTIFY_MASK | Gdk.EventMask.ENTER_NOTIFY_MASK)
		self.connect("leave-notify-event", self.on_leave)
		self.connect("enter-notify-event", self.on_enter)
		self.entered = False
		
		self.parent = parent
		self.trk = trk
		self.grid = Gtk.Grid()
		self.grid.set_column_spacing(3)
		self.grid.set_row_spacing(3)

		if trk:
			button = Gtk.Button()
			icon = Gio.ThemedIcon(name="edit-delete")
			image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
			button.add(image)
			button.connect("clicked", self.on_remove_button_clicked)
			button.set_tooltip_text("ctrl r")
			self.grid.attach(button, 3, 0, 1, 1)

			button = Gtk.Button()
			icon = Gio.ThemedIcon(name="list-remove")
			image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
			button.add(image)
			button.connect("clicked", self.on_retract_button_clicked)
			button.set_tooltip_text("ctrl -")
			self.grid.attach(button, 0, 0, 1, 1)

			button = Gtk.Button()
			icon = Gio.ThemedIcon(name="list-add")
			image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
			button.add(image)
			button.connect("clicked", self.on_expand_button_clicked)
			button.set_tooltip_text("ctrl +")
			self.grid.attach(button, 1, 0, 2, 1)

			button = Gtk.Button()
			icon = Gio.ThemedIcon(name="go-previous")
			image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
			button.add(image)
			button.connect("clicked", self.on_move_left_button_clicked)
			button.set_tooltip_text("ctrl left")
			self.grid.attach(button, 1, 1, 1, 1)

			button = Gtk.Button()
			icon = Gio.ThemedIcon(name="go-next")
			image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
			button.add(image)
			button.connect("clicked", self.on_move_right_button_clicked)
			button.set_tooltip_text("ctrl right")
			self.grid.attach(button, 2, 1, 1, 1)

			button = Gtk.Button()
			icon = Gio.ThemedIcon(name="go-first")
			image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
			button.add(image)
			button.connect("clicked", self.on_move_first_button_clicked)
			button.set_tooltip_text("ctrl left")
			self.grid.attach(button, 0, 1, 1, 1)

			button = Gtk.Button()
			icon = Gio.ThemedIcon(name="go-last")
			image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
			button.add(image)
			button.connect("clicked", self.on_move_last_button_clicked)
			button.set_tooltip_text("ctrl right")
			self.grid.attach(button, 3, 1, 1, 1)

			self.port_adj = Gtk.Adjustment(0, 0, 15, 1.0, 1.0)
			self.port_button = Gtk.SpinButton()
			self.port_button.set_adjustment(self.port_adj)
			self.port_adj.set_value(trk.port)
			self.port_adj.connect("value-changed", self.on_port_changed)

			lbl = Gtk.Label("port:")
			lbl.set_xalign(1.0)

			self.grid.attach(lbl, 0, 3, 1, 1)
			self.grid.attach(self.port_button, 1, 3, 2, 1)

			self.channel_adj = Gtk.Adjustment(1, 1, 16, 1.0, 1.0)
			self.channel_button = Gtk.SpinButton()
			self.channel_button.set_adjustment(self.channel_adj)
			self.channel_adj.set_value(trk.channel)
			self.channel_adj.connect("value-changed", self.on_channel_changed)

			lbl = Gtk.Label("channel:")
			lbl.set_xalign(1.0)
			
			self.grid.attach(lbl, 0, 2, 1, 1)
			self.grid.attach(self.channel_button, 1, 2, 2, 1)

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

	def popup(self):
		self.nrows_adj.set_value(self.trk.nrows)
		self.nsrows_adj.set_value(self.trk.nsrows)
		super().popup()

	def on_leave(self, wdg, prm):
		if prm.detail == Gdk.NotifyType.NONLINEAR:
				wdg.popdown()
				self.entered = False

	def on_enter(self, wdg, prm):
		if prm.detail == Gdk.NotifyType.NONLINEAR:
			if self.entered == 0:
				self.entered = True

	def on_remove_button_clicked(self, switch):
		TrackView.leave_all()
		self.parent.del_track()
					
	def on_retract_button_clicked(self, switch):
		self.trk.del_column()
		TrackView.leave_all()
		self.parent.seqview.redraw_track(self.trk)
		self.parent.redraw()
			
	def on_expand_button_clicked(self, switch):
		self.trk.add_column()
		TrackView.leave_all()
		self.parent.seqview.redraw_track(self.trk)
		self.parent.redraw()
			
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
		if (wdg.get_active()):
			self.nrows_button.set_sensitive(True)
			self.nsrows_check_button.set_sensitive(True)		
		else:
			self.nrows_button.set_sensitive(False)
			self.nrows_check_button.set_active(False)
			self.nrows_adj.set_value(self.nsrows_adj.get_value())
								
	def on_nsrows_toggled(self, wdg):
		if (wdg.get_active()):
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
	