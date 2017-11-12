import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio
import cairo
from pypms import pms
from trackviewpointer import trackviewpointer
from trackundobuffer import TrackUndoBuffer
from poormanspiano import PoorMansPiano

class TrackView(Gtk.DrawingArea):
	track_views = []
	
	def leave_all():
		for wdg in TrackView.track_views:
			redr = False
			if wdg.hover or wdg.edit:
				redr = True
				
			wdg.hover = None
			wdg.edit = None
			
			if redr:
				wdg.redraw()
					
	def __init__(self, seq, trk, parent):
		super(TrackView, self).__init__()
	
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
		self.parent = parent
		self._pointer = trackviewpointer(self, trk, seq)
		self.txt_width = 0
		self.txt_height = 0
		self.spacing = 1.0
		self.pmp = PoorMansPiano()
	
		if trk:
			self.undo_buff = TrackUndoBuffer(trk)
			
		self._surface = None
		self._context = None

		self.hover = None
		self.edit = None

		self.set_can_focus(True)

		TrackView.track_views.append(self)

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
		
			self.txt_height = float(height) * self.spacing * pms.cfg.seq_spacing
			self.txt_width = int(dx)

			nw = dx
			nh = (self.txt_height * self.seq.length) + 10
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

				if self.hover and r == self.hover[1]:
					cr.set_source_rgb(*(col * pms.cfg.intensity_txt_highlight * 1.2 for col in pms.cfg.colour))
				else:
					if pms.cfg.highlight > 1 and (r) % pms.cfg.highlight == 0:
						cr.set_source_rgb(*(col * pms.cfg.intensity_txt_highlight for col in pms.cfg.colour))
					else:
						cr.set_source_rgb(*(col * pms.cfg.intensity_txt for col in pms.cfg.colour))

				yy = (r + 1) * self.txt_height - ((self.txt_height - height) / 2)
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

		self.txt_height = float(height) * self.spacing * pms.cfg.seq_spacing
		self.txt_width = int(dx)

		nw = self.txt_width * len(self.trk)
		nh = (self.txt_height * self.trk.nrows) + 5
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
				
				if self.hover and r == self.hover[1] and c == self.hover[0]:
					cr.set_source_rgb(*(col * pms.cfg.intensity_txt_highlight * 1.2 for col in pms.cfg.colour))
				else:
					if pms.cfg.highlight > 1 and (r) % pms.cfg.highlight == 0:
						cr.set_source_rgb(*(col * pms.cfg.intensity_txt_highlight for col in pms.cfg.colour))
					else:
						cr.set_source_rgb(*(col * pms.cfg.intensity_txt for col in pms.cfg.colour))
		
				if self.edit and r == self.edit[1] and c == self.edit[0]:
					cr.rectangle(c * self.txt_width, (r * self.txt_height) + self.txt_height * .1, (self.txt_width / 8.0) * 7.2, self.txt_height * .9)
					cr.fill()
					cr.set_source_rgb(*(col * pms.cfg.intensity_background for col in pms.cfg.colour))
						
				yy = (r + 1) * self.txt_height - ((self.txt_height - height) / 2)
				
				cr.move_to((c * self.txt_width) + x, yy)
				
				rw = self.trk[c][r]
								
				if rw.type == 1: #note_on
					cr.show_text("%3s %03d" % (str(rw), rw.velocity))
				
				if rw.type == 2: #note_off
					cr.show_text("%3s" % (str(rw)))
					
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
		oh = self.hover
				
		new_hover_row = int(event.y / self.txt_height)
		new_hover_column = int(event.x / self.txt_width)
		self.hover = new_hover_column, new_hover_row
		
		if (self.hover != oh):
			if oh:
				self.redraw(oh[1])
				
			self.redraw(self.hover[1])
		
		if not self.trk:
			return False
		
		if pms.active_track:
			if not pms.active_track.edit:
				self.parent.change_active_track(self)
		else:
			self.parent.change_active_track(self)
			
		return False
		
	def on_button_press(self, widget, event):
		if not self.trk:
			return
		
		row = int(event.y / self.txt_height)
		col = int(event.x / self.txt_width)
		offs = int(event.x) % int(self.txt_width)
		
		enter_edit = False
		
		if not self.trk[col][row].type:	# empty
			enter_edit = True
			
		if self.trk[col][row].type == 2:# note_off
			enter_edit = True
		
		if offs < self.txt_width / 2.0:	# edit note
			enter_edit = True
		else: 							# edit velocity
			pass

		if enter_edit:
			TrackView.leave_all()
			self.parent.change_active_track(self)
			
			olded = self.edit
			self.edit = col, row
			self.redraw(row)
			if olded:
				self.redraw(olded[1])
			return True		
		
		return True
		
	def on_button_release(self, widget, event):
		return False

	def on_leave(self, wdg, prm):
		if self.hover:
			oh = self.hover
			self.hover = None
			self.redraw(oh[1])
		
	def on_enter(self, wdg, prm):
		pass

	# sheer madness :)
	def go_right(self, skip_track = False, rev = False):
		old = self.edit[1] 
		inc = 1
		if rev:
			inc *= - 1

		if not skip_track:
			self.edit = self.edit[0] + inc, self.edit[1]
			
			if self.edit[0] >= len(self.trk):
				self.go_right(True)
				pms.active_track.edit = 0, pms.active_track.edit[1]
				pms.active_track.redraw()
				return
				
			if self.edit[0] < 0:
				self.go_left(True)
				pms.active_track.edit = len(pms.active_track.trk) - 1, pms.active_track.edit[1]
				pms.active_track.redraw()
				return
				
			self.redraw(old)
			self.redraw(self.edit[1])
			return
		else:
			curr = None
			for i, trk, in enumerate(self.seq):
				if trk.index == self.trk.index:
					curr = i
			
			curr += inc
			if curr >= len(self.seq):
				curr = 0
			
			if curr < 0:
				curr = len(self.seq) - 1

			trk = self.parent.get_tracks()[curr]
			
			if trk == self:
				return

			old = self.edit
			self.edit = None
			self.parent.change_active_track(trk)
			
			trk.edit = 0, int(round((old[1] * self.spacing) / trk.spacing))
			trk.redraw(trk.edit[1])
			
			self.redraw(old[1])
			
	def go_left(self, skip_track = False, rev = True):
		self.go_right(skip_track, rev)

	def on_key_press(self, widget, event):
		if not self.trk:
			return
		
		#print("key : %d" % (event.keyval))
			
		if event.state & Gdk.ModifierType.CONTROL_MASK:
			if event.keyval == 122:			# z
				self.undo_buff.restore()
				self.parent.redraw_track(self.trk)
				#for wdg in self.parent._prop_view._track_box.get_children():
				#	wdg.redraw()
				return True

		note = self.pmp.key2note(event.keyval)
				
		if not self.edit:
			return False

		if note:
			self.undo_buff.add_state()
			old = self.edit[1]
			self.trk[self.edit[0]][self.edit[1]] = note
			self.trk[self.edit[0]][self.edit[1]].velocity = pms.cfg.velocity
			
			self.edit = self.edit[0], self.edit[1] + pms.cfg.skip
			if self.edit[1] >= self.trk.nrows:
				self.edit = self.edit[0], self.edit[1] - self.trk.nrows
			
			while self.edit[1] < 0:
				self.edit = self.edit[0], self.edit[1] + self.trk.nrows
			self.redraw(self.edit[1])
			self.redraw(old)
			self.undo_buff.add_state()
			return True
				
		if event.keyval == 65307:			# esc
			old = self.edit[1]
			self.edit = None
			self.redraw(old)
			return True
			
		if event.keyval == 65364:			# down
			old = self.edit[1]
			self.edit = self.edit[0], self.edit[1] + 1
			if self.edit[1] >= self.trk.nrows:
				self.edit = self.edit[0], 0
			
			self.redraw(old)
			self.redraw(self.edit[1])
			return True
		
		if event.keyval == 65362:			# up
			old = self.edit[1]
			self.edit = self.edit[0], self.edit[1] - 1
			if self.edit[1] < 0:
				self.edit = self.edit[0], self.trk.nrows - 1
			self.redraw(old)
			self.redraw(self.edit[1])
			return True
		
		if event.keyval == 65363:			# right
			self.go_right()
			return True
		
		if event.keyval == 65361:			# left
			self.go_left()
			return True

		if event.keyval == 65366:			# page-down
			old = self.edit[1]
			
			self.edit = self.edit[0], self.edit[1] + 1
			while not self.edit[1] % pms.cfg.highlight == 0:
				self.edit = self.edit[0], self.edit[1] + 1
			
			if self.edit[1] >= self.trk.nrows:
				self.edit = self.edit[0], self.trk.nrows - 1
			
			self.redraw(old)
			self.redraw(self.edit[1])
			return True
		
		if event.keyval == 65365:			# page-up
			old = self.edit[1]
			
			self.edit = self.edit[0], self.edit[1] - 1
			while not self.edit[1] % pms.cfg.highlight == 0:
				self.edit = self.edit[0], self.edit[1] - 1
				if self.edit[1] < 0:
					self.edit = self.edit[0], 0
			
			if self.edit[1] < 0:
				self.edit = self.edit[0], self.trk.nrows - 1
			self.redraw(old)
			self.redraw(self.edit[1])
			return True
		
		if event.keyval == 65056:			# shift-tab
			self.go_left(True)
			return True

		if event.keyval == 65289:			# tab
			self.go_right(True)
			return True
		
		if event.keyval == 65535:			# del
			self.trk[self.edit[0]][self.edit[1]].clear()
			self.redraw(self.edit[1])
			
			if event.state & Gdk.ModifierType.CONTROL_MASK:
				x = self.edit[0]
				y = self.edit[1]
				
				for y in range(self.edit[1], self.trk.nrows - 1):
					self.trk[x][y].copy(self.trk[x][y + 1])
					self.redraw(y)
		
				self.trk[x][self.trk.nrows -1].clear()
				self.redraw(self.trk.nrows -1)
			else:
				old = self.edit[1]
				self.edit = self.edit[0], self.edit[1] + pms.cfg.skip
				if self.edit[1] >= self.trk.nrows:
					self.edit = self.edit[0], self.trk.nrows - 1
					
				self.redraw(self.edit[1])
				self.redraw(old)

			self.undo_buff.add_state()
			return True

		if event.keyval == 92:				# | note_off
			self.trk[self.edit[0]][self.edit[1]].clear()
			self.trk[self.edit[0]][self.edit[1]].type = 2
			
			old = self.edit[1]
			self.edit = self.edit[0], self.edit[1] + pms.cfg.skip

			if self.edit[1] >= self.trk.nrows:
				self.edit = self.edit[0], self.edit[1] - self.trk.nrows
			
			while self.edit[1] < 0:
				self.edit = self.edit[0], self.edit[1] + self.trk.nrows
					
			self.redraw(self.edit[1])
			self.redraw(old)
			
			self.undo_buff.add_state()

		if event.keyval == 65379:			# insert
			self.undo_buff.add_state()
			if event.state & Gdk.ModifierType.CONTROL_MASK:
				self.undo_buff.add_state()
				x = self.edit[0]
				y = self.edit[1]
				
				for y in reversed(range(self.edit[1], self.trk.nrows - 1)):
					self.trk[x][y + 1].copy(self.trk[x][y])
					self.redraw(y + 1)
		
				self.trk[x][y].clear()
				self.redraw(y)
				self.undo_buff.add_state()
			return True
		
		if event.keyval == 65360:			# home
			old = self.edit[1]
			self.edit = self.edit[0], 0 
			self.redraw(self.edit[1])
			self.redraw(old)
			return True
		
		if event.keyval == 65367:			# end
			old = self.edit[1]
			self.edit = self.edit[0], self.trk.nrows - 1
			self.redraw(self.edit[1])
			self.redraw(old)
			return True
		
		return False

	def on_key_release(self, widget, event):
		if not self.trk:
			return
		
		#print("key : %d" % (event.keyval))
			
		note = self.pmp.key2note(event.keyval, True)
		return False
