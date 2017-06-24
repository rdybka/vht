import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio
import cairo

class TrackerView(Gtk.DrawingArea):
	def __init__(self):
		Gtk.DrawingArea.__init__(self)
		self.connect("draw", self.on_draw);
		#self.connect("realize", self.on_realize)
		
	def on_realize(self, widget):
		pass
		
	def on_draw(self, widget, cr):
		w = widget.get_allocated_width()
		h = widget.get_allocated_height()
		cr.set_source_rgb(0,.3,0)
		cr.rectangle(0, 0, w, h)
		cr.fill()
		
		cr.set_source_rgb(0, .8, 0)
		cr.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD )
		cr.set_font_size(12)
		cr.move_to(10, 10)
		for b in range(10):
			for a in range(32):
				cr.move_to(b * 40, a * 12)	
				cr.show_text("---")

