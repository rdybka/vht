import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio
import cairo
from threading import Lock
from pypms import pms

class TrackView(Gtk.DrawingArea):
	def __init__(self, trk):
		Gtk.DrawingArea.__init__(self)
	
		self.connect("draw", self.on_draw)
		self.connect("realize", self.on_realize)

		self.trk = trk
		self.highlight = 4
		self.padding = 3
	
	def on_realize(self, wdg):
		self.set_size_request(1, 1)
	
	def on_draw(self, widget, cr):
		if not self.trk:
			return
			
		w = widget.get_allocated_width()
		h = widget.get_allocated_height()
		cr.set_source_rgb(0,.3,0)
		cr.rectangle(0, 0, w, h)
		cr.fill()
		
		cr.set_source_rgb(0, .8, 0)
		cr.select_font_face(pms.seq_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
		cr.set_font_size(pms.seq_font_size)
		(x, y, width, height, dx, dy) = cr.text_extents("000 000")
		self._width = len(self.trk) * (width + (self.padding * 2)) + self.padding * 2
		self._height = ((height + (self.padding)) * self.trk.nrows) + self.padding
		if w != self._width or h != self._height:
			self.set_size_request(self._width, self._height)				
		
		for c in range(len(self.trk)):
			for r in range(self.trk.nrows):
				if (r) % self.highlight == 0:
					cr.set_source_rgb(0, 1, 0)		
				else:
					cr.set_source_rgb(0, .7, 0)
					
				cr.move_to(self.padding + c * (self.padding * 2 + width), (r + 1) * (height + self.padding))
				
				rw = self.trk[c][r]
								
				if rw.type == 1: #note_on
					cr.show_text("%3s %03d" % (str(rw), rw.velocity))
					
				if rw.type == 0: #none
					cr.show_text("---")

		pos = self.trk.pos
		if pos != 0.0:
			yy = int(pos * (height + self.padding))
			cr.move_to(0, yy)
			cr.line_to(w, yy)
			cr.stroke()					

		cr.set_source_rgb(0, .5, 0)
		cr.move_to(len(self.trk) * (width + (self.padding * 2)) + self.padding, self.padding)
		cr.line_to(len(self.trk) * (width + (self.padding * 2)) + self.padding, ((height + (self.padding)) * self.trk.nrows) - self.padding)
		cr.stroke()
