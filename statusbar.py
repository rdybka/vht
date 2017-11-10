import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio
import cairo
from pypms import pms
from trackview import TrackView
class StatusBar(Gtk.DrawingArea):
	def __init__(self):
		super(StatusBar, self).__init__()
		self.connect("draw", self.on_draw)
		self.connect("configure-event", self.on_configure)		
		self._surface = None
		self._context = None
		self.min_char_width = 60
		
		self.add_tick_callback(self.tick)

	def redraw(self):
		cr = self._context
		w = self.get_allocated_width()
		h = self.get_allocated_height()
		
		self._context.select_font_face(pms.cfg.seq_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)	
		fs = pms.cfg.seq_font_size
		
		(x, y, width, height, dx, dy) = cr.text_extents("PMS" * self.min_char_width)
		
		fits = False
		while not fits:
			self._context.set_font_size(fs)
			(x, y, width, height, dx, dy) = cr.text_extents("X" * self.min_char_width)
			if w > width:
				fits = True
			else:
				fs -= 1

		self.set_size_request(1, height * 1.5)

		gradient = cairo.LinearGradient(0, 0, 0, h)
		gradient.add_color_stop_rgb(0.0, *(col *  pms.cfg.intensity_txt_highlight for col in pms.cfg.colour))
		gradient.add_color_stop_rgb(1.0, *(col * pms.cfg.intensity_background for col in pms.cfg.colour))
		cr.set_source(gradient)
		
		cr.rectangle(0, 0, w, h)
		cr.fill()

		cr.set_source_rgb(*(col * 0 for col in pms.cfg.colour))
		
		txt = ""
		
		trk = TrackView.active_track
				
		t = 0
		r = 0
		c = 0
		cs = pms.curr_seq
		
		if trk:
			t = trk.trk.index
			if trk.edit:
				c = trk.edit[0]
				r = trk.edit[1]
			
		txt += "%02d:%02d:%02d:%03d" % (cs, t, c, r)
		txt += " oct:%d vel:%d hig:%d skp:%d bpm:%d" % (pms.cfg.octave, pms.cfg.velocity, pms.cfg.highlight, pms.cfg.skip, pms.bpm)
		
		h = height * 1.25
		cr.move_to(x, h)
		cr.show_text(txt)			
		
		txt = "%02d:%03d.%03d ***" % (cs, int(pms[cs].pos), (pms[cs].pos - int(pms[cs].pos)) * 1000)
		(x, y, width, height, dx, dy) = cr.text_extents(txt)
		cr.move_to(w - dx, h)
		cr.show_text(txt)			
		
		cr.move_to(0, 0)
		cr.line_to(w, 0)
		cr.stroke()

		self.queue_draw()

	def tick(self, wdg, param):
		self.redraw()
		return 1	

	def on_configure(self, wdg, event):
		if self._surface:
			self._surface.finish()

		self._surface = wdg.get_window().create_similar_surface(cairo.CONTENT_COLOR,
			wdg.get_allocated_width(),
			wdg.get_allocated_height())

		self._context = cairo.Context(self._surface)
		self._context.set_antialias(cairo.ANTIALIAS_NONE)
		self._context.set_line_width((pms.cfg.seq_font_size / 6.0) * pms.cfg.seq_line_width)
		self.redraw()
		return True

	def on_draw(self, widget, cr):
		cr.set_source_surface(self._surface, 0, 0)
		cr.paint()
		return False
