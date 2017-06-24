import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio
import cairo

class TrackerView(Gtk.DrawingArea):
	def __init__(self):
		Gtk.DrawingArea.__init__(self)
		self.connect("draw", self.on_draw);
		#self.connect("realize", self.on_realize)
		
		self.highlight = 4
		
	def on_realize(self, widget):
		pass
		
	def on_draw(self, widget, cr):
		w = widget.get_allocated_width()
		h = widget.get_allocated_height()
		cr.set_source_rgb(0,.3,0)
		cr.rectangle(0, 0, w, h)
		cr.fill()
		
		cr.set_source_rgb(0, .8, 0)
		cr.select_font_face("Roboto Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL )
		cr.set_font_size(12)
		cr.move_to(10, 10)
		
		for b in range(16):
			for a in range(65):
				if (a - 1 ) % self.highlight == 0:
					cr.set_source_rgb(0, 1, 0)		
				else:
					cr.set_source_rgb(0, .7, 0)
					
				cr.move_to(30 + b * 40, a * 12)	
				cr.show_text("---")
		
		cr.select_font_face("Roboto Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD )
		for y in range(65):
			if (y - 1) % self.highlight == 0:
				cr.set_source_rgb(0, 1, 0)		
			else:
				cr.set_source_rgb(0, .7, 0)

			cr.move_to(0, y * 12)
			cr.show_text("%03d" % (y))		
	

