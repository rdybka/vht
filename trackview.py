import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio
import cairo
from pypms import pms
from trackviewpointer import trackviewpointer
class TrackView(Gtk.DrawingArea):
	track_views = []
	active_track = None
	def on_leave_all():
		for wdg in TrackView.track_views:
			wdg.hover_row = -1
			wdg.redraw()
					
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
		self._pointer = trackviewpointer(self, trk, seq)
		self.highlight = pms.cfg.highlight
		self.txt_width = 0
		self.txt_height = 0
		self.spacing = 1.0
	
		self._surface = None
		self._context = None

		self.focus = False
		self.hover = False
		self.hover_row = -1
		self.edit_row = None

		self.set_can_focus(True)

		self.track_views.append(self)

	def __del__(self):
		if self._surface:
			self._surface.finish()

	def tick(self):
		if self._context:
			if self.trk:
				self._pointer.draw(self.trk.pos)
			else:
				self._pointer.draw(self.seq.pos)
			return True
				
	def on_configure(self, wdg, event):
		if self._surface:
			self._surface.finish()

		self._surface = wdg.get_window().create_similar_surface(cairo.CONTENT_COLOR,
			wdg.get_allocated_width(),
			wdg.get_allocated_height())

		self._context = cairo.Context(self._surface)
		self._context.set_antialias(cairo.ANTIALIAS_NONE)
		self._context.set_line_width((pms.cfg.seq_font_size / 6.0) * pms.cfg.seq_line_width)
		
		self.tick()
		self.redraw()
		return True

	def redraw(self, from_row = -666, to_row = -666):
		cr = self._context

		self._context.select_font_face(pms.cfg.seq_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
		self._context.set_font_size(pms.cfg.seq_font_size)
				
		w = self.get_allocated_width()
		h = self.get_allocated_height()
		
		wnd = self.get_window()
		ir = Gdk.Rectangle()
		
		complete = False
		if from_row == -666 and to_row == -666:
			complete = True
			
		if from_row != -666 and to_row == -666:
			to_row = from_row

		if from_row > to_row:
			a = to_row
			to_row = from_row
			from_row = a
		
		# side_column
		if not self.trk:
			(x, y, width, height, dx, dy) = cr.text_extents("000|")
		
			self.txt_height = float(height) * self.spacing
			self.txt_width = int(dx)

			nw = dx
			nh = (self.txt_height * self.seq.length) + 5
			self.set_size_request(nw, nh)
				
			if complete:
				cr.set_source_rgb(*(col * pms.cfg.intensity_background for col in pms.cfg.colour))	
				cr.rectangle(0, 0, w, h)
				cr.fill()
		
			rows_to_draw = []
	
			if complete:
				rows_to_draw = range(self.seq.length)
			else:
				for r in range(self.seq.length):
					if r >= from_row and r <= to_row:
						rows_to_draw.append(r)
		
			for r in rows_to_draw:
				if not complete: # redraw background
					cr.set_source_rgb(*(col * pms.cfg.intensity_background for col in pms.cfg.colour))	
					cr.rectangle(0, r * self.txt_height, w, self.txt_height)
					cr.fill()

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
				
				if not complete:
					ir.x = 0
					ir.width = w
					ir.y = int(r * self.txt_height)
					ir.height = self.txt_height * 2
					wnd.invalidate_rect(ir, False)

			(x, y, width, height, dx, dy) = cr.text_extents("|")
			cr.set_source_rgb(*(col * pms.cfg.intensity_lines for col in pms.cfg.colour))
			cr.set_antialias(cairo.ANTIALIAS_NONE)
			cr.move_to(self.txt_width - (dx / 2), 0)
			cr.line_to(self.txt_width - (dx / 2), (self.seq.length) * self.txt_height)
			cr.stroke()

			if complete:
				self.queue_draw()
			return
			
		(x, y, width, height, dx, dy) = cr.text_extents("000 000|")

		self.txt_height = float(height) * self.spacing
		self.txt_width = int(dx)

		nw = self.txt_width * len(self.trk)
		nh = self.txt_height * self.trk.nrows
		self.set_size_request(nw, nh)
		
		if complete:
			cr.set_source_rgb(*(col * pms.cfg.intensity_background for col in pms.cfg.colour))	
			cr.rectangle(0, 0, w, h)
			cr.fill()
		
		for c in range(len(self.trk)):
			rows_to_draw = []
		
			if complete:
				rows_to_draw = range(self.trk.nrows)
			else:
				for r in range(self.trk.nrows):
					if r >= from_row and r <= to_row:
						rows_to_draw.append(r)
	
			for r in rows_to_draw:
				if not complete: # redraw background
					cr.set_source_rgb(*(col * pms.cfg.intensity_background for col in pms.cfg.colour))	
					cr.rectangle(c * self.txt_width, r * self.txt_height, self.txt_width + 5, self.txt_height)
					cr.fill()
				
				if r == self.hover_row:
					cr.set_source_rgb(*(col * pms.cfg.intensity_txt_highlight * 1.2 for col in pms.cfg.colour))
				else:
					if (r) % self.highlight == 0:
						cr.set_source_rgb(*(col * pms.cfg.intensity_txt_highlight for col in pms.cfg.colour))
					else:
						cr.set_source_rgb(*(col * pms.cfg.intensity_txt for col in pms.cfg.colour))
		
				yy = int((r + 1) * self.txt_height)
				cr.move_to((c * self.txt_width) + x, yy)
				
				rw = self.trk[c][r]
								
				if rw.type == 1: #note_on
					cr.show_text("%3s %03d" % (str(rw), rw.velocity))
					
				if rw.type == 0: #none
					cr.show_text("---    ")

				if not complete:
					ir.x = 0
					ir.width = w
					ir.y = r * self.txt_height
					ir.height = self.txt_height * 2
					wnd.invalidate_rect(ir, False)

		(x, y, width, height, dx, dy) = cr.text_extents("0")
		cr.set_source_rgb(*(col * pms.cfg.intensity_lines for col in pms.cfg.colour))
		cr.move_to(self.txt_width * len(self.trk) - (width / 2), 0)
		cr.line_to(self.txt_width * len(self.trk) - (width / 2), (self.trk.nrows) * self.txt_height)
		cr.stroke()

		if complete:
			self.queue_draw()
			
	def on_draw(self, widget, cr):
		cr.set_source_surface(self._surface, 0, 0)
		cr.paint()
		return False

	def on_motion(self, widget, event):
		x = event.x
		y = event.y
		
		new_hover_row = int(y / self.txt_height)
		if (new_hover_row != self.hover_row):
			oh = self.hover_row
			self.hover_row = new_hover_row
			if oh >= 0:
				self.redraw(oh)
			self.redraw(self.hover_row)
			
		TrackView.active_track = self
		return False
		
	def on_button_press(self, widget, event):
		print("butt down")
		return False

	def on_button_release(self, widget, event):
		print("butt up")
		return False

	def on_leave(self, wdg, prm):
		oh = self.hover_row
		self.hover_row = -1
		if oh >= 0:
			self.redraw(oh)
		
	def on_enter(self, wdg, prm):
		pass
		#self.grab_focus()
	
	def on_key_press(self, widget, event):
		print("key")
		#if event.keyval == 65507 or event.keyval == 65508:
		return False

	def on_key_release(self, widget, event):
		return False
