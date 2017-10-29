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

		self.connect("draw", self.on_draw)
		self.connect("realize", self.on_realize)

		self.seq = seq
		self.trk = trk
		self.propview = propview
		self.seqview = seqview
		self.padding = 3
		self.button_rect = Gdk.Rectangle()

		self.clear_popups = pms.clear_popups
				
		self.set_events(Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.BUTTON_PRESS_MASK )
		self.connect("button-press-event", self.on_click)
		self.connect("motion-notify-event", self.on_mouse_move)

		if trk:
			self.popover = TrackPropViewPopover(self, trk)
		else:
			self.popover = SequencePropViewPopover(self, seq)
			
		self.popover.set_position(Gtk.PositionType.BOTTOM)
		self.popover.set_modal(False)
		self.popover.set_transitions_enabled(False)
	
	def on_realize(self, wdg):
		self.set_size_request(1, 1)
	
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

	def on_draw(self, widget, cr):
		w = widget.get_allocated_width()
		h = widget.get_allocated_height()
		cr.set_source_rgb(*(col * pms.cfg.intensity_background for col in pms.cfg.colour))
		cr.rectangle(0, 0, w, h)
		cr.fill()

		cr.select_font_face(pms.cfg.seq_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
		cr.set_font_size(pms.cfg.seq_font_size)
			
		if self.trk == None:
			(x, y, width, height, dx, dy) = cr.text_extents("000|")
			self._txt_height = dy
			self.txt_width = dx
			self._width = dx
			self._height = int(height * 2)
				
			self.set_size_request(self._width, self._height)
				
			cr.set_source_rgb(*(col * pms.cfg.intensity_background for col in pms.cfg.colour))
			cr.rectangle(0, 0, w, h)
			cr.fill()			
				
			cr.set_source_rgb(*(col * pms.cfg.intensity_txt for col in pms.cfg.colour))
			cr.set_source_rgb(*(col * pms.cfg.intensity_lines for col in pms.cfg.colour))			
			yy = height
			cr.move_to(x, yy)	
			cr.show_text("   |")
			yy += height
			cr.move_to(x, yy)	
			cr.set_source_rgb(*(col * pms.cfg.intensity_lines for col in pms.cfg.colour))
			cr.show_text("   |")
			cr.move_to(x, yy)		
			cr.set_source_rgb(*(col * pms.cfg.intensity_txt_highlight for col in pms.cfg.colour))
			cr.show_text("***")
				
			self.button_rect.width = width
			self.button_rect.height = height + 5
			self.button_rect.x = x;
			self.button_rect.y = height
			self.popover.set_pointing_to(self.button_rect)
			return

		(x, y, width, height, dx, dy) = cr.text_extents("000 000|")
		
		self._txt_height = dy
		self.txt_width = dx * len(self.trk)
		self._height = int(height * 2)
				
		self.set_size_request(self.txt_width, self._height)
				
		cr.set_source_rgb(*(col * pms.cfg.intensity_background for col in pms.cfg.colour))
		cr.rectangle(0, 0, w, h)
		cr.fill()			
				
		cr.set_source_rgb(*(col * pms.cfg.intensity_txt for col in pms.cfg.colour))
			
		yy = height
		cr.move_to(x, yy)	
		cr.show_text("p%02d c%02d" % (self.trk.port, self.trk.channel))
		
		self.button_rect.width = (dx / 8.0) * 3.0
		self.button_rect.height = height
				
		self.button_rect.x = x + (dx * (len(self.trk) - 1) + dx / 2)
		self.button_rect.y = height
		self.popover.set_pointing_to(self.button_rect)
		
		for l in range(len(self.trk) - 2):
			cr.move_to(x + (dx) * (l + 1), yy)	
			cr.show_text("--------")

		if len(self.trk) > 1:
			cr.move_to(x + (dx) * (len(self.trk) -1), yy)	
			cr.show_text("-------")

		# *** button
		cr.set_source_rgb(*(col * pms.cfg.intensity_lines for col in pms.cfg.colour))
		cr.move_to(x + (dx) * (len(self.trk) - 1), yy)	
		cr.show_text("       +")
		yy += height
		cr.move_to(x + (dx) * (len(self.trk) - 1), yy)	
		cr.show_text("       |")
	
		cr.set_source_rgb(*(col * pms.cfg.intensity_txt_highlight for col in pms.cfg.colour))
		cr.move_to(x + (dx) * (len(self.trk) - 1), yy)	
		cr.show_text("    ***")
		
		
		

