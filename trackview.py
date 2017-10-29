import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio
import cairo
from pypms import pms
from trackviewpointer import TrackViewPointer

class TrackView(Gtk.Overlay):
	def __init__(self, trk):
		Gtk.Overlay.__init__(self)
	
		self._dr = Gtk.DrawingArea()
		self._dr.connect("draw", self.on_draw)
		self._dr.connect("configure-event", self.on_configure)
		
		self._dr.connect("motion-notify-event", self.on_motion)
		self._dr.connect("button-press-event", self.on_button)
		
		self.trk = trk
		self.highlight = pms.cfg.highlight
		self.padding = pms.cfg.padding
		self.txt_width = 0

		self.spacing = 1.0
	
		self._width = 0
		self._txt_height = 0
		self._surface = None
		self._context = None

		self.add(self._dr)
		
		self._ptr = TrackViewPointer(trk, self)
		
		self.add_overlay(self._ptr)
		self.show_all()

	def __del__(self):
		if self._surface:
			self._surface.finish()

	def tick(self):
		self._ptr.set_pos(self.trk.pos)
		return True
				
	def on_configure(self, wdg, event):
		if self._surface:
			self._surface.finish()

		self._surface = wdg.get_window().create_similar_surface(cairo.CONTENT_COLOR,
			wdg.get_allocated_width(),
			wdg.get_allocated_height())

		self._context = cairo.Context(self._surface)
		self.tick()
		self.redraw()
		return True

	def on_motion(self, widget, event):
		pass
		
	def on_button(self, widget, event):
		pass
	
	def redraw(self):
		cr = self._context
				
		w = self.get_allocated_width()
		h = self.get_allocated_height()

		cr.select_font_face(pms.cfg.seq_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
		cr.set_font_size(pms.cfg.seq_font_size)
		(x, y, width, height, dx, dy) = cr.text_extents("000 000")
		
		self._txt_height = height
		self.txt_width = width
		self._width = int(len(self.trk) * (width + (self.padding * 2)) + self.padding * 2)
		self._height = int(((height + (self.padding)) * (self.trk.nrows * self.spacing)) + self.padding)
		
		self.set_size_request(self._width, self._height)
				
		cr.set_source_rgb(*(col * pms.cfg.intensity_background for col in pms.cfg.colour))
		cr.rectangle(0, 0, w, h)
		cr.fill()
		
		for c in range(len(self.trk)):
			for r in range(self.trk.nrows):
				if (r) % self.highlight == 0:
					cr.set_source_rgb(*(col * pms.cfg.intensity_txt_highlight for col in pms.cfg.colour))
				else:
					cr.set_source_rgb(*(col * pms.cfg.intensity_txt for col in pms.cfg.colour))
		
				yy = ((r * self.spacing)+ 1) * (height + self.padding)
				
				cr.move_to(self.padding + c * (self.padding * 2 + width), yy)
				
				rw = self.trk[c][r]
								
				if rw.type == 1: #note_on
					cr.show_text("%3s %03d" % (str(rw), rw.velocity))
					
				if rw.type == 0: #none
					cr.show_text("---")

		cr.set_source_rgb(*(col * pms.cfg.intensity_lines for col in pms.cfg.colour))
		cr.move_to(int(len(self.trk)) * (width + (self.padding * 2)) + self.padding, self.padding)
		cr.line_to(int(len(self.trk)) * (width + (self.padding * 2)) + self.padding, ((height + (self.padding)) * self.trk.nrows * self.spacing) - self.padding)
		cr.stroke()

	
	def on_draw(self, widget, cr):
		w = self.get_allocated_width()
		if self._width != w:
			self.redraw()
		
		cr.set_source_surface(self._surface, 0, 0)
		cr.paint()

		return False
