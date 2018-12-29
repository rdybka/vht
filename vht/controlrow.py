import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio
import cairo

from vht import *

class ControlRow(Gtk.ActionBar):
	def __init__(self, trk, ctrlnum):
		super(ControlRow, self).__init__()

		self.trk = trk
		self.ctrlnum = ctrlnum

		button = Gtk.Button()
		icon = Gio.ThemedIcon(name="go-up")
		image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
		button.add(image)
		#button.connect("clicked", self.on_stop_button_activate)
		self.pack_start(button)
		
		button = Gtk.Button()
		icon = Gio.ThemedIcon(name="go-down")
		image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
		button.add(image)
		#button.connect("clicked", self.on_stop_button_activate)
		self.pack_start(button)
		
		button = Gtk.ToggleButton()
		icon = Gio.ThemedIcon(name="media-record")
		image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
		button.add(image)
		#button.connect("clicked", self.on_stop_button_activate)
		self.pack_start(button)
		
		self.ctrl_adj = Gtk.Adjustment(1, 1, 127, 1.0, 1.0)
		self.ctrl_button = Gtk.SpinButton()
		self.ctrl_button.set_adjustment(self.ctrl_adj)
		self.ctrl_adj.set_value(self.ctrlnum)
		#self.nsrows_adj.connect("value-changed", self.on_nsrows_changed)
		self.pack_start(self.ctrl_button)
		
		button = Gtk.Button()
		if ctrlnum == -1:
			icon = Gio.ThemedIcon(name="list-add")
		else:
			icon = Gio.ThemedIcon(name="edit-delete")

		image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
		button.add(image)
		#button.connect("clicked", self.on_stop_button_activate)
		self.pack_end(button)

		self.show_all()
