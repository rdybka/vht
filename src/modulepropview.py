import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio
import cairo

from libvht import vht

class ModulePropView(Gtk.Box):
	def __init__(self, seqview):
		super(Gtk.Box, self).__init__()

		self.seqview = seqview
		self.grid = Gtk.Grid()
		self.grid.set_column_spacing(3)
		self.grid.set_row_spacing(3)

		self.highlight_adj = Gtk.Adjustment(0, 1, 16, 1.0, 1.0)
		self.highlight_button = Gtk.SpinButton()
		self.highlight_button.set_adjustment(self.highlight_adj)
		self.highlight_adj.set_value(vht.cfg.highlight)
		self.highlight_adj.connect("value-changed", self.on_highlight_changed)

		self.grid.attach(Gtk.Label("highlight:"), 0, 0, 1, 1)
		self.grid.attach(self.highlight_button, 1, 0, 2, 1)
		
		self.octave_adj = Gtk.Adjustment(0, 0, 8, 1.0, 1.0)
		self.octave_button = Gtk.SpinButton()
		self.octave_adj.set_value(vht.cfg.octave)
		self.octave_button.set_adjustment(self.octave_adj)
		self.octave_adj.connect("value-changed", self.on_octave_changed)

		self.grid.attach(Gtk.Label("octave:"), 0, 1, 1, 1)
		self.grid.attach(self.octave_button, 1, 1, 2, 1)
	
		self.skip_adj = Gtk.Adjustment(0, -16, 16, 1.0, 1.0)
		self.skip_button = Gtk.SpinButton()
		self.skip_adj.set_value(vht.cfg.skip)
		self.skip_button.set_adjustment(self.skip_adj)
		self.skip_adj.connect("value-changed", self.on_skip_changed)

		self.grid.attach(Gtk.Label("skip:"), 3, 0, 1, 1)
		self.grid.attach(self.skip_button, 4, 0, 2, 1)

		self.vel_adj = Gtk.Adjustment(0, 0, 127, 1.0, 1.0)
		self.vel_button = Gtk.SpinButton()
		self.vel_adj.set_value(vht.cfg.velocity)
		self.vel_button.set_adjustment(self.vel_adj)
		self.vel_adj.connect("value-changed", self.on_vel_changed)

		self.grid.attach(Gtk.Label("velocity:"), 3, 1, 1, 1)
		self.grid.attach(self.vel_button, 4, 1, 2, 1)
				
		self.pack_end(self.grid, False, True, 0)
		self.show_all()
		
		vht.update_modulepropview = self.update
		self.update()

	def update(self):
		self.highlight_adj.set_value(vht.cfg.highlight)
		self.octave_adj.set_value(vht.cfg.octave)
		self.skip_adj.set_value(vht.cfg.skip)
		
	def on_highlight_changed(self, adj):
		vht.cfg.highlight = int(adj.get_value())
		self.seqview.redraw_track(None)

	def on_octave_changed(self, adj):
		vht.cfg.octave = int(adj.get_value())

	def on_skip_changed(self, adj):
		vht.cfg.skip = int(adj.get_value())

	def on_vel_changed(self, adj):
		vht.cfg.velocity = int(adj.get_value())
