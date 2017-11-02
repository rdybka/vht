import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio
import cairo
from pypms import pms

class TrackView(Gtk.DrawingArea):
	track_views = []
	
	def on_leave_all():
		for wdg in TrackView.track_views:
			wdg.hover_row = None
			wdg.redraw()
			wdg.queue_draw()
		
	def __init__(self, seq, trk):
		Gtk.DrawingArea.__init__(self)
	
		self.set_events(Gdk.EventMask.POINTER_MOTION_MASK |
			Gdk.EventMask.BUTTON_PRESS_MASK |
			Gdk.EventMask.BUTTON_RELEASE_MASK |
			Gdk.EventMask.LEAVE_NOTIFY_MASK | 
			Gdk.EventMask.ENTER_NOTIFY_MASK |
			Gdk.EventMask.KEY_PRESS_MASK |
			Gdk.EventMask.KEY_RELEASE_MASK)

		self.connect("draw", self.on_draw)
		self.connect("configure-event", self.on_configure)
		self.connect("motion-notify-event", self.on_motion)
		self.connect("button-press-event", self.on_button_press)
		self.connect("button-release-event", self.on_button_release)
		self.connect("key-press-event", self.on_key_press)
		self.connect("key-release-event", self.on_key_release)	
		self.connect("enter-notify-event", self.on_enter)
		self.connect("leave-notify-event", self.on_leave)
		
		self.seq = seq
		self.trk = trk
		self.highlight = pms.cfg.highlight
		self.padding = pms.cfg.padding
		self.txt_width = 0
		self.txt_height = 0;
		self.spacing = 1.0
	
		self._surface = None
		self._context = None

		self.focus = False
		self.hover = False
		self.hover_row = None
		self.edit_row = None

		self.set_can_focus(True)

		self.track_views.append(self)

	def __del__(self):
		if self._surface:
			self._surface.finish()

	def tick(self):
		if self.trk:
			self._ptr.set_pos(self.trk.pos)
		else:
			self._ptr.set_pos(self.seq.pos)
		return True
				
	def on_configure(self, wdg, event):
		self._ptr.height = pms.cfg.pointer_height

		if self._surface:
			self._surface.finish()

		self._surface = wdg.get_window().create_similar_surface(cairo.CONTENT_COLOR,
			wdg.get_allocated_width(),
			wdg.get_allocated_height())

		self._context = cairo.Context(self._surface)
		self.tick()
		self.redraw()
		return True

	def redraw(self):
		cr = self._context
				
		w = self.get_allocated_width()
		h = self.get_allocated_height()

		cr.select_font_face(pms.cfg.seq_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
		cr.set_font_size(pms.cfg.seq_font_size)
		
		if not self.trk:
			(x, y, width, height, dx, dy) = cr.text_extents("000|")
		
			self.txt_height = float(height) * self.spacing
			self.txt_width = dx

			self.set_size_request(dx, (self.txt_height * self.seq.length) + 5)

			cr.set_source_rgb(*(col * pms.cfg.intensity_background for col in pms.cfg.colour))
				
			cr.rectangle(0, 0, w, h)
			cr.fill()
		
			for r in range(self.seq.length):
				if r == self.hover_row:
					cr.set_source_rgb(*(col * pms.cfg.intensity_txt_highlight * 1.2 for col in pms.cfg.colour))
				else:
					if (r) % self.highlight == 0:
						cr.set_source_rgb(*(col * pms.cfg.intensity_txt_highlight for col in pms.cfg.colour))
					else:
						cr.set_source_rgb(*(col * pms.cfg.intensity_txt for col in pms.cfg.colour))

				yy = (r + 1) * self.txt_height
				cr.move_to(x, yy)
				cr.show_text("%03d" % r)

				cr.set_source_rgb(*(col * pms.cfg.intensity_lines for col in pms.cfg.colour))
				cr.move_to(x, yy)
				cr.show_text("   |")
				
			return
			
		(x, y, width, height, dx, dy) = cr.text_extents("000 000|")
		self.txt_height = float(height) * self.spacing
		self.txt_width = dx
		
		self.set_size_request(self.txt_width * len(self.trk), self.txt_height * self.trk.nrows)
		cr.set_source_rgb(*(col * pms.cfg.intensity_background for col in pms.cfg.colour))
		
		cr.rectangle(0, 0, w, h)
		cr.fill()
		
		for c in range(len(self.trk)):
			margin = " "
			if c == len(self.trk) - 1:
				margin = "|"
				
			for r in range(self.trk.nrows):
				if r == self.hover_row:
					cr.set_source_rgb(*(col * pms.cfg.intensity_txt_highlight * 1.2 for col in pms.cfg.colour))
				else:
					if (r) % self.highlight == 0:
						cr.set_source_rgb(*(col * pms.cfg.intensity_txt_highlight for col in pms.cfg.colour))
					else:
						cr.set_source_rgb(*(col * pms.cfg.intensity_txt for col in pms.cfg.colour))
		
				yy = (r + 1) * self.txt_height
				cr.move_to((c * self.txt_width) + x, yy)	
				
				rw = self.trk[c][r]
								
				if rw.type == 1: #note_on
					cr.show_text("%3s %03d" % (str(rw), rw.velocity))
					
				if rw.type == 0: #none
					cr.show_text("---    ")

				if len(margin):
					cr.set_source_rgb(*(col * pms.cfg.intensity_lines for col in pms.cfg.colour))
					cr.move_to((c * self.txt_width) + x, yy)
					cr.show_text("       %c" % (margin))

	def on_draw(self, widget, cr):
		cr.set_source_surface(self._surface, 0, 0)
		cr.paint()
		return False

	def on_motion(self, widget, event):
		x = event.x
		y = event.y
		self.hover_row = int(y / self.txt_height)
		self.redraw()
		self.queue_draw()
		return False
		
	def on_button_press(self, widget, event):
		return False

	def on_button_release(self, widget, event):
		return False

	def on_leave(self, wdg, prm):
		if self._ptr.stole_mouse:
			self._ptr.stole_mouse = False
			return
			
		self.hover_row = None
		wdg.redraw()
		wdg.queue_draw()
		
	def on_enter(self, wdg, prm):
		for wdg in self.track_views:
			if wdg != self:
				wdg.hover_row = None
				wdg.redraw()
				
		x = prm.x
		y = prm.y
		self.hover_row = int(y / self.txt_height)
		
		self.grab_focus()
		self.redraw()
		self.queue_draw()
	
	def on_key_press(self, widget, event):
		print("key")
		#if event.keyval == 65507 or event.keyval == 65508:
		return False

	def on_key_release(self, widget, event):
		return False
