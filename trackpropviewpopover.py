import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gdk, Gtk, Gio
import cairo

class TrackPropViewPopover(Gtk.Popover):
	def __init__(self, parent, trk):
		Gtk.Popover.__init__(self)
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
			self.grid.attach(button, 2, 0, 1, 1)

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
			self.grid.attach(button, 1, 0, 1, 1)

			button = Gtk.Button()
			icon = Gio.ThemedIcon(name="go-previous")
			image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
			button.add(image)
			button.connect("clicked", self.on_move_left_button_clicked)
			button.set_tooltip_text("ctrl left")
			self.grid.attach(button, 0, 1, 1, 1)

			button = Gtk.Button()
			icon = Gio.ThemedIcon(name="go-next")
			image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
			button.add(image)
			button.connect("clicked", self.on_move_right_button_clicked)
			button.set_tooltip_text("ctrl right")
			self.grid.attach(button, 2, 1, 1, 1)

			self.port_adj = Gtk.Adjustment(0, 0, 15, 1.0, 1.0)
			self.port_button = Gtk.SpinButton()
			self.port_button.set_adjustment(self.port_adj)
			self.port_adj.set_value(trk.port)
			self.port_adj.connect("value-changed", self.on_port_changed)

			lbl = Gtk.Label("port:")
			lbl.set_xalign(1.0)

			self.grid.attach(lbl, 0, 2, 1, 1)
			self.grid.attach(self.port_button, 1, 2, 1, 1)

			self.channel_adj = Gtk.Adjustment(1, 1, 16, 1.0, 1.0)
			self.channel_button = Gtk.SpinButton()
			self.channel_button.set_adjustment(self.channel_adj)
			self.channel_adj.set_value(trk.channel)
			self.channel_adj.connect("value-changed", self.on_channel_changed)

			lbl = Gtk.Label("channel:")
			lbl.set_xalign(1.0)
			
			self.grid.attach(lbl, 0, 3, 1, 1)
			self.grid.attach(self.channel_button, 1, 3, 1, 1)

			self.nrows_adj = Gtk.Adjustment(1, 0, 256, 1.0, 1.0)
			self.nrows_button = Gtk.SpinButton()
			self.nrows_button.set_adjustment(self.nrows_adj)
			self.nrows_adj.set_value(trk.nrows)
			self.nrows_adj.connect("value-changed", self.on_nrows_changed)

			lbl = Gtk.Label("nrows")
			lbl.set_xalign(1.0)
		
			self.grid.attach(lbl, 0, 4, 1, 1)
			self.grid.attach(self.nrows_button, 1, 4, 1, 1)

			self.grid.show_all()
			self.add(self.grid)

	def on_leave(self, wdg, prm):
		if prm.detail == Gdk.NotifyType.NONLINEAR:
				wdg.popdown()
				self.entered = False

	def on_enter(self, wdg, prm):
		if prm.detail == Gdk.NotifyType.NONLINEAR:
			if self.entered == 0:
				self.entered = True

	def on_remove_button_clicked(self, switch):
		self.parent.del_track()
					
	def on_retract_button_clicked(self, switch):
		self.trk.del_column()
			
	def on_expand_button_clicked(self, switch):
		self.trk.add_column()
			
	def on_port_changed(self, adj):
		self.trk.port = int(adj.get_value())

	def on_channel_changed(self, adj):
		self.trk.channel = int(adj.get_value())

	def on_nrows_changed(self, adj):
		self.trk.nrows = int(adj.get_value())

	def on_move_left_button_clicked(self, switch):
		self.parent.move_left()
		
	def on_move_right_button_clicked(self, switch):
		self.parent.move_right()
		
