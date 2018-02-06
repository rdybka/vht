import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio
import cairo

from vht import *

class BlackGrid(Gtk.Grid):
	def __init__(self):
		Gtk.Grid.__init__(self)
		
		self.connect("draw", self.on_draw)
		
	def on_draw(self, widget, cr):
		w = widget.get_allocated_width()
		h = widget.get_allocated_height()
		cr.set_source_rgb(*(col * cfg.intensity_background for col in cfg.colour))
		cr.rectangle(0, 0, w, h)
		cr.fill()
		return False
