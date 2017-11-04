import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio
import cairo

from threading import Lock

from trackpropviewpopover import TrackPropViewPopover
from sequencepropviewpopover import SequencePropViewPopover
from pypms import pms

class TrackPropView(Gtk.DrawingArea):
	def __init__(self, trk = None, seq = None, seqview = None, propview = None):
		Gtk.DrawingArea.__init__(self)

		self.set_events(Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.BUTTON_PRESS_MASK )
		self.connect("button-press-event", self.on_click)
		self.connect("motion-notify-event", self.on_mouse_move)
		self.connect("draw", self.on_draw)
		self.connect("configure-event", self.on_configure)

		self.seq = seq
		self.trk = trk
		self.propview = propview
		self.seqview = seqview
		self.txt_width = 0
		self.txt_height = 0
		self.button_rect = Gdk.Rectangle()
		self._surface = None
		self._context = None

		if trk:
			self.popover = TrackPropViewPopover(self, trk)
		else:
			self.popover = SequencePropViewPopover(self, seq)
			
		self.popover.set_position(Gtk.PositionType.BOTTOM)
		self.popover.set_modal(False)
		self.popover.set_transitions_enabled(False)

		self.clear_popups = pms.clear_popups
	
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
	
	def add_track(self):
		port = 0
		channel = 1
		if (len(self.seq)):
			port = self.seq[-1].port
			channel = self.seq[-1].channel

		trk = self.seq.add_track(port, channel)
		self.seqview.add_track(trk)
		self.propview.add_track(trk)
		self.seqview.redraw_track(trk)
	
	def del_track(self):
		self.popover.popdown()
		self.seqview.del_track(self.trk)
		self.propview.del_track(self.trk)
		self.seqview.redraw_track(None)
		self.destroy()
		
	def move_left(self):
		self.propview.move_left(self.trk)

	def move_right(self):
		self.propview.move_right(self.trk)
	
	def move_first(self):
		self.propview.move_first(self.trk)

	def move_last(self):
		self.propview.move_last(self.trk)
	
	def on_mouse_move(self, widget, data):
		if data.x >= self.button_rect.x:
			if data.x <= self.button_rect.x + self.button_rect.width:
				if data.y >= self.button_rect.y:
					if data.y <= self.button_rect.y + self.button_rect.height:		
						self.clear_popups()
						self.popover.popup()
						return
		
	def on_click(self, widget, data):
		pass 

	def redraw(self):
		self.queue_draw()
		
		cr = self._context
		
		self._context.select_font_face(pms.cfg.seq_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
		self._context.set_font_size(pms.cfg.seq_font_size)
				
		w = self.get_allocated_width()
		h = self.get_allocated_height()
		
		cr.set_source_rgb(*(col * pms.cfg.intensity_background for col in pms.cfg.colour))
		cr.rectangle(0, 0, w, h)
		cr.fill()

		cr.select_font_face(pms.cfg.seq_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
		cr.set_font_size(pms.cfg.seq_font_size)
			
		if self.trk == None:
			(x, y, width, height, dx, dy) = cr.text_extents("000|")
			self.txt_height = height
			self.txt_width = int(dx)

			self.set_size_request(self.txt_width, self.txt_height * 2)
				
			cr.set_source_rgb(*(col * pms.cfg.intensity_background for col in pms.cfg.colour))
			cr.rectangle(0, 0, w, h)
			cr.fill()			
				
			cr.move_to(x, self.txt_height * 2)		
			cr.set_source_rgb(*(col * pms.cfg.intensity_txt_highlight for col in pms.cfg.colour))
			cr.show_text("***")
				
			self.button_rect.width = width
			self.button_rect.height = height + 5
			self.button_rect.x = x;
			self.button_rect.y = height
			self.popover.set_pointing_to(self.button_rect)
			
			cr.set_line_width((pms.cfg.seq_font_size / 6.0) * pms.cfg.seq_line_width)
			(x, y, width, height, dx, dy) = cr.text_extents("|")
			cr.set_source_rgb(*(col * pms.cfg.intensity_lines for col in pms.cfg.colour))
			cr.set_antialias(cairo.ANTIALIAS_NONE)
			cr.move_to(self.txt_width - (dx / 2), self.txt_height * .3)
			cr.line_to(self.txt_width - (dx / 2), (self.seq.length) * self.txt_height)
			cr.stroke()
			return

		(x, y, width, height, dx, dy) = cr.text_extents("000 000|")

		self.txt_height = height
		self.txt_width = int(dx)

		nw = self.txt_width * len(self.trk)
		nh = self.txt_height * self.trk.nrows
		self.set_size_request(nw, nh)
		
		cr.set_source_rgb(*(col * pms.cfg.intensity_background for col in pms.cfg.colour))	
		cr.rectangle(0, 0, w, h)
		cr.fill()
		
		self.set_size_request(self.txt_width * len(self.trk), self.txt_height * 2)
				
		cr.set_source_rgb(*(col * pms.cfg.intensity_txt for col in pms.cfg.colour))
			
		cr.move_to(x, self.txt_height)	
		cr.show_text("p%02d c%02d" % (self.trk.port, self.trk.channel))
		
		self.button_rect.width = (dx / 8.0) * 3.0
		self.button_rect.height = height
				
		self.button_rect.x = x + (dx * (len(self.trk) - 1) + dx / 2)
		self.button_rect.y = height
		self.popover.set_pointing_to(self.button_rect)
		
		cr.set_source_rgb(*(col * pms.cfg.intensity_txt_highlight for col in pms.cfg.colour))
		cr.move_to(x + (dx) * (len(self.trk) - 1), self.txt_height * 2)	
		cr.show_text("    ***")

		cr.set_line_width((pms.cfg.seq_font_size / 6.0) * pms.cfg.seq_line_width)

		(x, y, width, height, dx, dy) = cr.text_extents("0")
		cr.set_source_rgb(*(col * pms.cfg.intensity_lines for col in pms.cfg.colour))
		
		cr.move_to(self.txt_width * len(self.trk) - (width / 2), self.txt_height * .3)
		cr.line_to(self.txt_width * len(self.trk) - (width / 2), 2 * self.txt_height)
		cr.stroke()
				
	def on_draw(self, widget, cr):
		cr.set_source_surface(self._surface, 0, 0)
		cr.paint()
		return False
