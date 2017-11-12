import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio
import cairo

from pypms import pms
from pypms.pmssequence import PMSSequence

class trackviewpointer():
	def __init__(self, parent, trk, seq):
		self.trk = trk
		if not trk:
			self.trk = seq
			
		self.spacing = 1.0
		self.opacity = pms.cfg.pointer_opacity
	
		self._parent = parent
		
		self.height = pms.cfg.seq_font_size
		#self.y = 0
		#self.yy = 0

		self.lpos = None

		self.stopped = False

	def draw(self, pos):
		if not pms.playing and pos == 0:
			if self.stopped:
				return
			
			self._parent.redraw()
			self.stopped = True
			return

		self.stopped = False

		h = self._parent.get_allocated_height()
		w = self._parent.get_allocated_width()
		self.height = pms.cfg.seq_font_size
		cr = self._parent._context
		
		y = pos - 1
		yy = 3
		if y < 0:
			y = 0
		
		if self.lpos:
			self._parent.redraw(self.lpos - 2, self.lpos + 2)
			
		self._parent.redraw(pos - 2, pos + 2)
		self.lpos = pos

		y = pos * self._parent.txt_height
		y -= self.height / 2.0
			
		yy = h - (y + self.height)
						
		r = int(self.trk.pos)
		
		if isinstance(self.trk, PMSSequence):
			i = .5
			if pms.cfg.highlight > 1 and (r) % pms.cfg.highlight == 0:
				i *= 2
			
			x = 0
			xx = (self._parent.txt_width / 4.0) * 3.1

			gradient = cairo.LinearGradient(x, y, x, y + self.height)
			gradient.add_color_stop_rgba(0.0, *(col * i for col in pms.cfg.colour), 0)
			gradient.add_color_stop_rgba(0.5, *(col * i for col in pms.cfg.colour), self.opacity)
			gradient.add_color_stop_rgba(1.0, *(col * i for col in pms.cfg.colour), 0)
			cr.set_source(gradient)
			
			cr.rectangle(x, y, xx, self.height)
			cr.fill()

			if int(pos) == 0:
				self._parent.redraw(self._parent.seq.length -1)
				
				cr.set_source_rgb(*(col * pms.cfg.intensity_background for col in pms.cfg.colour))	
				cr.rectangle(0, self._parent.seq.length * self._parent.txt_height, w, self._parent.txt_height)
				cr.fill()
				
			return

		r = int(self.trk.pos)
		if r < 0 or r >= self.trk.nrows:
			return

		for c in range(len(self.trk)):
			i = .5
			if pms.cfg.highlight > 1 and (r) % pms.cfg.highlight == 0:
				i *= 1.0

			rw = self.trk[c][r]
			
			if rw.type == 1:
				i *= 1.5 + 2.0 * (self.trk.pos - r)
			
			x = c * self._parent.txt_width
			xx = (self._parent.txt_width / 8.0) * 7.2

			gradient = cairo.LinearGradient(x, y, x, y + self.height)
			gradient.add_color_stop_rgba(0.0, *(col * i for col in pms.cfg.colour), 0)
			gradient.add_color_stop_rgba(0.5, *(col * i for col in pms.cfg.colour), self.opacity)
			gradient.add_color_stop_rgba(1.0, *(col * i for col in pms.cfg.colour), 0)
			cr.set_source(gradient)
						
			cr.rectangle(x, y, xx, self.height)
			cr.fill()

		if int(pos) == 0:
			self._parent.redraw(self.trk.nrows -1)
			cr.set_source_rgb(*(col * pms.cfg.intensity_background for col in pms.cfg.colour))	
			cr.rectangle(0, self.trk.nrows * self._parent.txt_height, w, self._parent.txt_height)
			cr.fill()
				
