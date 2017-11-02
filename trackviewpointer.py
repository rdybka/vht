import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio
import cairo

from pypms import pms
import pypms
from pypms.pmssequence import PMSSequence

class TrackViewPointer(Gtk.DrawingArea):
	def __init__(self, trk, seq, parent):
		Gtk.DrawingArea.__init__(self)

		self.set_events(Gdk.EventMask.ENTER_NOTIFY_MASK)

		self.connect("draw", self.on_draw)
		self.connect("configure-event", self.on_configure)
		self.connect("enter-notify-event", self.on_enter)
				
		self.stole_mouse = False
		
		self.trk = trk
		if not trk:
			self.trk = seq
			
		self.highlight = pms.cfg.highlight
		self.padding = pms.cfg.padding
		self.spacing = 1.0
	
		self._parent = parent
		self._width = 0
		
		self.height = pms.cfg.pointer_height
		self.drawn = False

		self._surface = None
		self._context = None
		self.set_opacity(pms.cfg.pointer_opacity)
		#self.set_sensitive(False)
		
	def __del__(self):
		if self._surface:
			self._surface.finish()
	
	def on_configure(self, wdg, event):
		if self._surface:
			self._surface.finish()

		self._surface = wdg.get_window().create_similar_surface(cairo.CONTENT_COLOR,
			wdg.get_allocated_width(),
			wdg.get_allocated_height())

		self._context = cairo.Context(self._surface)
		self.redraw()
		return True

	def set_pos(self, pos):
		if not pms.playing and pos == 0:
			self.hide()
			return
			
		h = self._parent.get_allocated_height()
		
		self.set_margin_top(0)
		self.set_margin_bottom(0)
		y = pos * self._parent.txt_height
		y -= self.height / 2
			
		yy = h - (y + self.height)
			
		if yy < 0:
			yy = 0
							
		if y < 0:
			y = 0
			
		self.set_margin_top(y)
		self.set_margin_bottom(yy)
						
		self.show()
	
	def on_motion(self, widget, event):
		pass
		
	def on_button(self, widget, event):
		pass
	
	def redraw(self):
		cr = self._context
				
		w = self._parent.get_allocated_width()

		cr.set_source_rgb(*(col * pms.cfg.intensity_background for col in pms.cfg.colour))

		cr.rectangle(0, 0, w, self.height + 5)
		cr.fill()

		r = int(self.trk.pos)
		
		if isinstance(self.trk, PMSSequence):
			i = .5
			if (r) % self.highlight == 0:
				i *= 2
			
			cr.set_source_rgb(*(col * i for col in pms.cfg.colour))
		
			x = 0
			xx = (self._parent.txt_width / 4.0) * 3.2
			
			cr.rectangle(x, 0, xx, self.height + 5)
			cr.fill()
			return

		r = int(self.trk.pos)
		if r < 0 or r >= self.trk.nrows:
			return

		for c in range(len(self.trk)):
			i = .5
			if (r) % self.highlight == 0:
				i *= 1.0

			rw = self.trk[c][r]
			
			if rw.type == 1:
				i *= 1.5 + 2.0 * (self.trk.pos - r)
			
			cr.set_source_rgb(*(col * i for col in pms.cfg.colour))
			
			x = c * self._parent.txt_width
			xx = (self._parent.txt_width / 8.0) * 7.2
			
			cr.rectangle(x, 0, xx, self.height + 5)
			cr.fill()

	def on_draw(self, widget, cr):
		cr.set_source_surface(self._surface, 0, 0)
		cr.paint()
		return False

	def on_enter(self, widget, prm):
		self.stole_mouse = True

