import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio
import cairo

class TrackView(Gtk.DrawingArea):
	def __init__(self, tracknum = None):
		Gtk.DrawingArea.__init__(self)
		self.connect("draw", self.on_draw);
		#self.connect("realize", self.on_realize)
		self.tracknum = tracknum
			
		self.highlight = 4
		self.nrows = 32
		self.padding = 3
		
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
		(x, y, width, height, dx, dy) = cr.text_extents("000")
		
		if w != (width + (self.padding * 2)):
			self.set_size_request(width + (self.padding * 2), ((height + (self.padding)) * self.nrows) + self.padding)
		
		if self.tracknum:
			for a in range(self.nrows + 1):
				if (a - 1 ) % self.highlight == 0:
					cr.set_source_rgb(0, 1, 0)		
				else:
					cr.set_source_rgb(0, .7, 0)
					
				cr.move_to(self.padding, a * (height + self.padding))	
				cr.show_text("---")
		
		if not self.tracknum:
			cr.select_font_face("Roboto Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD )
			for y in range(self.nrows + 1):
				if (y - 1) % self.highlight == 0:
					cr.set_source_rgb(0, 1, 0)		
				else:
					cr.set_source_rgb(0, .7, 0)

				cr.move_to(self.padding, y * (height + self.padding))
				cr.show_text("%03d" % (y))		
	

