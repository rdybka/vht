import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gdk, Gtk, Gio
import cairo
from libvht import mod
from vht.trackviewpointer import trackviewpointer
from vht.trackundobuffer import TrackUndoBuffer
from vht.poormanspiano import PoorMansPiano

class TrackView(Gtk.DrawingArea):
	track_views = []
	clipboard = {}
	
	def leave_all():
		for wdg in TrackView.track_views:
			redr = False
			if wdg.hover or wdg.edit or wdg.select_start:
				redr = True
				
			wdg.hover = None
			wdg.edit = None
			wdg.select_start = None
			wdg.select_end = None
			
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
	
		self.drag = False
		self.sel_drag = False
		self.sel_dragged = False
		self.sel_drag_prev = None
		self.sel_drag_back = None
		self.sel_drag_front = None
		self.select = False
		self.select_start = None
		self.select_end = None
	
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
		self._context.set_line_width((mod.cfg.seq_font_size / 6.0) * mod.cfg.seq_line_width)
		
		self.tick()
		self.redraw()
		return True

	def redraw(self, from_row = -666, to_row = -666):
		cr = self._context

		self._context.select_font_face(mod.cfg.seq_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
		self._context.set_font_size(mod.cfg.seq_font_size)
				
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
		
			self.txt_height = float(height) * self.spacing * mod.cfg.seq_spacing
			self.txt_width = int(dx)

			nw = dx
			nh = (self.txt_height * self.seq.length) + 10
			self.set_size_request(nw, nh)
				
			if complete:
				cr.set_source_rgb(*(col * mod.cfg.intensity_background for col in mod.cfg.colour))	
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
					cr.set_source_rgb(*(col * mod.cfg.intensity_background for col in mod.cfg.colour))	
					cr.rectangle(0, r * self.txt_height, w, self.txt_height)
					cr.fill()

				if self.hover and r == self.hover[1]:
					cr.set_source_rgb(*(col * mod.cfg.intensity_txt_highlight * 1.2 for col in mod.cfg.colour))
				else:
					if mod.cfg.highlight > 1 and (r) % mod.cfg.highlight == 0:
						cr.set_source_rgb(*(col * mod.cfg.intensity_txt_highlight for col in mod.cfg.colour))
					else:
						cr.set_source_rgb(*(col * mod.cfg.intensity_txt for col in mod.cfg.colour))

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
			cr.set_source_rgb(*(col * mod.cfg.intensity_lines for col in mod.cfg.colour))
			cr.set_antialias(cairo.ANTIALIAS_NONE)
			cr.move_to(self.txt_width - (dx / 2), 0)
			cr.line_to(self.txt_width - (dx / 2), (self.seq.length) * self.txt_height)
			cr.stroke()

			if complete:
				self.queue_draw()
			return
			
		(x, y, width, height, dx, dy) = cr.text_extents("000 000|")

		self.txt_height = float(height) * self.spacing * mod.cfg.seq_spacing
		self.txt_width = int(dx)

		nw = self.txt_width * len(self.trk)
		nh = (self.txt_height * self.trk.nrows) + 5
		self.set_size_request(nw, nh)
		
		if complete:
			cr.set_source_rgb(*(col * mod.cfg.intensity_background for col in mod.cfg.colour))	
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
					cr.set_source_rgb(*(col * mod.cfg.intensity_background for col in mod.cfg.colour))	
					cr.rectangle(c * self.txt_width, r * self.txt_height, self.txt_width + 5, self.txt_height)
					cr.fill()
				
				if self.hover and r == self.hover[1] and c == self.hover[0]:
					cr.set_source_rgb(*(col * mod.cfg.intensity_txt_highlight * 1.2 for col in mod.cfg.colour))
				else:
					if mod.cfg.highlight > 1 and (r) % mod.cfg.highlight == 0:
						cr.set_source_rgb(*(col * mod.cfg.intensity_txt_highlight for col in mod.cfg.colour))
					else:
						cr.set_source_rgb(*(col * mod.cfg.intensity_txt for col in mod.cfg.colour))
	
				if self.select_start and self.select_end:
					ssx = self.select_start[0]
					ssy = self.select_start[1]
					sex = self.select_end[0]
					sey = self.select_end[1]
				
					if sex < ssx:
						xxx = sex
						sex	= ssx
						ssx = xxx
				
					if sey < ssy:
						yyy = sey
						sey = ssy
						ssy = yyy
					
					if c >= ssx and c <= sex and r >= ssy and r <= sey:
						cr.set_source_rgb(*(col * mod.cfg.intensity_select for col in mod.cfg.colour))
						if c == len(self.trk) - 1:
							cr.rectangle(c * self.txt_width, r * self.txt_height, (self.txt_width / 8.0) * 7.2, self.txt_height)
						else:
							cr.rectangle(c * self.txt_width, r * self.txt_height, self.txt_width, self.txt_height)
						cr.fill()
						cr.set_source_rgb(*(col * mod.cfg.intensity_background for col in mod.cfg.colour))

				if not self.select_start and not self.select_end:
					if self.edit and r == self.edit[1] and c == self.edit[0]:
						cr.set_source_rgb(*(mod.cfg.colour_record))
						
						cr.rectangle(c * self.txt_width, (r * self.txt_height) + self.txt_height * .1, (self.txt_width / 8.0) * 7.2, self.txt_height * .9)
						cr.fill()
						cr.set_source_rgb(*(col * mod.cfg.intensity_background for col in mod.cfg.colour))
						
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
		cr.set_source_rgb(*(col * mod.cfg.intensity_lines for col in mod.cfg.colour))
		cr.move_to(self.txt_width * len(self.trk) - (width / 2), 0)
		cr.line_to(self.txt_width * len(self.trk) - (width / 2), (self.trk.nrows) * self.txt_height)
		cr.stroke()

		if complete:
			self.queue_draw()
			
	def on_draw(self, widget, cr):
		cr.set_source_surface(self._surface, 0, 0)
		cr.paint()
		return False

	def swap_row(self, col, row, col2, row2):
		rw = self.trk[col][row]
		rw2 = self.trk[col2][row2]
		rw3 = self.trk[col][row]
		rw.copy(rw2)
		rw2.copy(rw3)
		
	def on_motion(self, widget, event):
		if not self.trk:
			return False
		
		new_hover_row = min(int(event.y / self.txt_height), self.trk.nrows - 1)
		new_hover_column = min(int(event.x / self.txt_width), len(self.trk) -1)

		new_hover_row = max(new_hover_row, 0)
		new_hover_column = max(new_hover_column, 0)
		
		if event.y > 50:
			mod.clear_popups()

		if self.select:
			if not self.select_start:
				self.select_start = self.edit
				self.select_end = self.select_start
			
			if self.select_end[1] != new_hover_row or self.select_end[0] != new_hover_column:
				self.select_end = new_hover_column, new_hover_row
				self.redraw()

		if self.drag:
			if self.trk[new_hover_column][new_hover_row].type == 0:		# dragging
				if self.edit[1] != new_hover_row or self.edit[0] != new_hover_column:
					old_row = self.edit[1]
					self.swap_row(self.edit[0], self.edit[1], new_hover_column, new_hover_row)
					self.edit = new_hover_column, new_hover_row
					
					self.redraw(new_hover_row)
					self.redraw(old_row)

		if self.sel_drag:
			dx = new_hover_column - self.sel_drag_prev[0]
			dy = new_hover_row - self.sel_drag_prev[1]
			sw = self.select_end[0] - self.select_start[0]
			sh = self.select_end[1] - self.select_start[1]
			
			if dx or dy:
				self.sel_dragged = True
				nx = self.select_start[0] + dx
				ny = self.select_start[1] + dy
								
				self.sel_drag_prev = new_hover_column, new_hover_row
				old = self.select_start[1], self.select_end[1]
				
				for r in self.sel_drag_front:
					nc = r[0] + self.select_start[0], r[1] + self.select_start[1]
					if self.select_start[1] > self.select_end[1]:
						nc = r[0] + self.select_end[0], r[1] + self.select_end[1]
					
					inbounds = True
					if nc[0] < 0 or nc[0] > len(self.trk) -1 or nc[1] < 0 or nc[1] > self.trk.nrows - 1:
						inbounds = False
						
					if inbounds:
						if nc in self.sel_drag_back:
							rr = self.sel_drag_back[nc]
							self.trk[nc[0]][nc[1]].type = rr[0]
							self.trk[nc[0]][nc[1]].note = rr[1]
							self.trk[nc[0]][nc[1]].velocity = rr[2]
							self.trk[nc[0]][nc[1]].delay = rr[3]
						else:
							self.trk[nc[0]][nc[1]].clear()
				
				self.select_start = nx, ny
				self.select_end = nx + sw, ny + sh
				
				for r in self.sel_drag_front:
					nc = r[0] + nx, r[1] + ny
					if self.select_end[1] < self.select_start[1]:
						nc = r[0] + self.select_end[0], r[1] + self.select_end[1]

					inbounds = True

					if nc[0] < 0 or nc[0] > len(self.trk) -1 or nc[1] < 0 or nc[1] > self.trk.nrows - 1:
						inbounds = False
					
					if inbounds:
						rr = self.sel_drag_front[r]
						self.trk[nc[0]][nc[1]].type = rr[0]
						self.trk[nc[0]][nc[1]].note = rr[1]
						self.trk[nc[0]][nc[1]].velocity = rr[2]
						self.trk[nc[0]][nc[1]].delay = rr[3]
				
				self.redraw(*(old))
				self.redraw(self.select_start[1], self.select_end[1])
				
		oh = self.hover
		self.hover = new_hover_column, new_hover_row
		
		if (self.hover != oh):
			if oh:
				self.redraw(oh[1])
				
			self.redraw(self.hover[1])
		
		if mod.active_track:
			if not mod.active_track.edit:
				self.parent.change_active_track(self)
		else:
			self.parent.change_active_track(self)
			
		return False
		
	def on_button_press(self, widget, event):
		if not self.trk:
			return
	
		shift = False
		if event.state & Gdk.ModifierType.SHIFT_MASK:
			shift = True	
		
		row = int(event.y / self.txt_height)
		col = int(event.x / self.txt_width)
		offs = int(event.x) % int(self.txt_width)

		if event.button == mod.cfg.delete_button:
			if self.trk[col][row].type == 0:
				trk = mod.active_track
				if trk:
					trk.edit = None
					trk.select_start = None
					trk.select_end = None
					trk.redraw()
					
				self.parent.change_active_track(self)
				return True
						
			self.trk[col][row].clear()
			self.redraw(row)
			self.undo_buff.add_state()
			return True
					
		enter_edit = False
		
		if event.button != mod.cfg.select_button:
			return False
		
		self.sel_drag = False
		self.sel_dragged = False
		if self.select_start:
			ssx = self.select_start[0]
			ssy = self.select_start[1]
			sex = self.select_end[0]
			sey = self.select_end[1]
				
			if sex < ssx:
				xxx = sex
				sex	= ssx
				ssx = xxx
				
			if sey < ssy:
				yyy = sey
				sey = ssy
				ssy = yyy
		
			if col >= ssx and col <= sex:
				if row >= ssy and row <= sey:
					self.sel_drag = True
					self.sel_drag_prev = col, row
					
					self.sel_drag_front = self.to_dict(True)
					self.sel_drag_back = self.to_dict()
					
					for r in self.sel_drag_front:
						del self.sel_drag_back[(r[0] + ssx, r[1] + ssy)]
				
					return True
				
		if not self.trk[col][row].type:	# empty
			enter_edit = True
			if not shift:
				self.select = True
				self.select_start = None
				self.select_end = None

		if self.trk[col][row].type == 1:# note_ob
			enter_edit = True
			self.drag = True
			
		if self.trk[col][row].type == 2:# note_off
			enter_edit = True
			self.drag = True
		
		if offs < self.txt_width / 2.0:	# edit note
			enter_edit = True
		else: 							# edit velocity
			enter_edit = True

		if enter_edit:
			if shift:
				self.select_end = col, row
				if self.select_start:
					self.select = True
					
				if self.edit: # new selection
					self.select = True
					self.select_start = self.edit
					self.select_end = col, row
				
				self.redraw()
				return True
			
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
		if self.sel_drag and event.button == mod.cfg.select_button:
			if self.sel_dragged:
				self.sel_drag = False
				self.undo_buff.add_state()
				# cap selection
				if self.select_start:
					ssx = max(self.select_start[0], 0)
					sex = max(self.select_end[0], 0)
					ssy = max(self.select_start[1], 0)
					sey = max(self.select_end[1], 0)
					
					ssx = min(ssx, len(self.trk) - 1)
					sex = min(sex, len(self.trk) - 1)
										
					ssy = min(ssy, self.trk.nrows - 1)
					sey = min(sey, self.trk.nrows - 1)
					self.select_start = ssx, ssy
					self.select_end = sex, sey
			else:
				row = int(event.y / self.txt_height)
				col = int(event.x / self.txt_width)
				self.sel_drag = False
				old = self.select_start[1], self.select_end[1]
				self.select_start = None
				self.select_end = None
				self.edit = col, row
				self.redraw(*(old))
				self.redraw(self.edit[1])
				return True
		
		if event.button == mod.cfg.select_button:
			self.select = None
			if self.select_start == self.select_end:
				self.select_start = None
				self.select_end = None
				if self.edit:
					self.redraw(self.edit[1])
			
			if self.select_start:
				self.edit = None
				# normalise selection
				ssx = self.select_start[0]
				ssy = self.select_start[1]
				sex = self.select_end[0]
				sey = self.select_end[1]
				
				if sex < ssx:
					xxx = sex
					sex	= ssx
					ssx = xxx
				
				if sey < ssy:
					yyy = sey
					sey = ssy
					ssy = yyy
			
				self.select_start = ssx, ssy
				self.select_end = sex, sey
		
			if self.drag:
				self.drag = False
				self.undo_buff.add_state()
				
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
				mod.active_track.edit = 0, mod.active_track.edit[1]
				mod.active_track.redraw()
				return
				
			if self.edit[0] < 0:
				self.go_left(True)
				mod.active_track.edit = len(mod.active_track.trk) - 1, mod.active_track.edit[1]
				mod.active_track.redraw()
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

	def selection(self):
		if not self.select_start or not self.select_end:
			return None
			
		ssx = self.select_start[0]
		ssy = self.select_start[1]
		sex = self.select_end[0]
		sey = self.select_end[1]
				
		if sex < ssx:
			xxx = sex
			sex	= ssx
			ssx = xxx
				
		if sey < ssy:
			yyy = sey
			sey = ssy
			ssy = yyy
		
		ret = []
		for x in range(ssx, sex + 1):
			for y in range(ssy, sey + 1):
				ret.append(self.trk[x][y])
		return ret

	def to_dict(self, sel_only = False):
		ret = {}
		if sel_only:
			ret = self.copy_selection(dest = ret)
			return ret
		
		for x in range(len(self.trk)):
			for y in range(self.trk.nrows):
				r = self.trk[x][y]
				if r.type:
					ret[(x, y)] = (r.type, r.note, r.velocity, r.delay)
		
		return ret

	def copy_selection(self, cut = False, dest = None):
		if not self.select_start or not self.select_end:
			return
			
		ssx = self.select_start[0]
		ssy = self.select_start[1]
		sex = self.select_end[0]
		sey = self.select_end[1]
				
		if sex < ssx:
			xxx = sex
			sex	= ssx
			ssx = xxx
				
		if sey < ssy:
			yyy = sey
			sey = ssy
			ssy = yyy
		
		d = dest
		if not d:
			d = TrackView.clipboard
			
		d.clear()
		
		for x in range(ssx, sex + 1):
			for y in range(ssy, sey + 1):
				r = self.trk[x][y]
				if r.type:
					d[(x - ssx, y - ssy)] = (r.type, r.note, r.velocity, r.delay)
				
				if cut:
					self.trk[x][y].clear()
		
		return d
		
	def paste(self):
		if not self.edit:
			return
			
		d = TrackView.clipboard
		dx = 0
		dy = 0
		
		for v in d.keys():
			dx = max(dx, v[0])
			dy = max(dy, v[1])

		while len(self.trk) - self.edit[0] < (dx + 1):
			self.trk.add_column()

		for k in d.keys():
			dx = self.edit[0] + k[0]
			dy = self.edit[1] + k[1]
			if (dy < self.trk.nrows):
				r = d[k]
				self.trk[dx][dy].type = r[0]
				self.trk[dx][dy].note = r[1]
				self.trk[dx][dy].velocity = r[2]
				self.trk[dx][dy].delay = r[3]
		
		self.redraw()

	def on_key_press(self, widget, event):
		if not self.trk:
			return

		shift = False
		if event.state & Gdk.ModifierType.SHIFT_MASK:
			shift = True

		ctrl = False
		if event.state & Gdk.ModifierType.CONTROL_MASK:
			ctrl = True

		alt = False
		if event.state & Gdk.ModifierType.MOD1_MASK:
			alt = True

		#print("key : %d %s" % (event.keyval, event.state))
			
		if ctrl:
			if event.keyval == 122:			# ctrl-z
				self.undo_buff.restore()
				self.parent.redraw_track(self.trk)
				return True

			if event.keyval == 99:			# ctrl-c
				self.copy_selection()
				return True

			if event.keyval == 120:			# ctrl-x
				self.undo_buff.add_state()
				self.copy_selection(True)
				self.redraw()
				return True

			if event.keyval == 118:			# ctrl-v
				self.undo_buff.add_state()	
				self.paste()
				self.redraw()
				self.undo_buff.add_state()
				self.parent._prop_view.redraw(self.trk.index)
				return True
			
			if event.keyval == 97:			# ctrl-a
				if self.edit:
					self.select_start = self.edit[0], 0
					self.select_end = self.edit[0], self.trk.nrows - 1
					self.edit = None
					self.redraw()
				elif self.select_start: 
					if self.select_start[1] == 0 and self.select_end[1] == self.trk.nrows -1:
						self.select_start = 0, 0
						self.select_end = len(self.trk) - 1, self.trk.nrows - 1
						self.redraw()
					else:
						self.select_start = self.select_start[0], 0
						self.select_end = self.select_start[0], self.trk.nrows - 1
						self.redraw()
				
				return True

		note = self.pmp.key2note(event.keyval)
				
		if self.edit and note:
			self.undo_buff.add_state()
			old = self.edit[1]
			self.trk[self.edit[0]][self.edit[1]] = note
			self.trk[self.edit[0]][self.edit[1]].velocity = mod.cfg.velocity
			
			self.edit = self.edit[0], self.edit[1] + mod.cfg.skip
			if self.edit[1] >= self.trk.nrows:
				self.edit = self.edit[0], self.edit[1] - self.trk.nrows
			
			while self.edit[1] < 0:
				self.edit = self.edit[0], self.edit[1] + self.trk.nrows
			self.redraw(self.edit[1])
			self.redraw(old)
			self.undo_buff.add_state()
			return True
		
		redr = False
		old = self.edit
				
		if self.edit and event.keyval == 65307:			# esc
			self.edit = None
			redr = True

		sel = self.selection()
		if self.edit:
			sel = []
			sel.append(self.trk[self.edit[0]][self.edit[1]])
			
		if sel and ctrl and event.keyval == 65362:	# ctrl+up on selection
			for r in sel:
				if r.type:
					r.note = min(r.note + 1, 127)
			
			self.undo_buff.add_state()
			if self.edit:
				self.redraw(self.edit[1])
			else:
				self.redraw(self.select_start[1], self.select_end[1])
			return True

		if sel and ctrl and event.keyval == 65365:	# ctrl+page up on selection
			for r in sel:
				if r.type:
					r.note = min(r.note + 12, 127)

			self.undo_buff.add_state()
			if self.edit:
				self.redraw(self.edit[1])
			else:
				self.redraw(self.select_start[1], self.select_end[1])
			return True
			
		if sel and ctrl and event.keyval == 65364:	# ctrl+down on selection
			for r in sel:
				if r.type:
					r.note = max(r.note - 1, 0)
			
			self.undo_buff.add_state()
			if self.edit:
				self.redraw(self.edit[1])
			else:
				self.redraw(self.select_start[1], self.select_end[1])
			return True
			
		if sel and ctrl and event.keyval == 65366:	# ctrl+page down on selection
			for r in sel:
				if r.type:
					r.note = max(r.note - 12, 0)
			
			self.undo_buff.add_state()
			if self.edit:
				self.redraw(self.edit[1])
			else:
				self.redraw(self.select_start[1], self.select_end[1])
			return True
			
		if sel and alt and event.keyval == 65362:	# alt+up on selection
			for r in sel:
				if r.type:
					r.velocity = min(r.velocity + 1, 127)
					mod.cfg.velocity = r.velocity
			
			self.undo_buff.add_state()
			if self.edit:
				self.redraw(self.edit[1])
			else:
				self.redraw(self.select_start[1], self.select_end[1])
			return True

		if sel and alt and event.keyval == 65365:	# alt+page up on selection
			for r in sel:
				if r.type:
					r.velocity = min(r.velocity + 10, 127)
					mod.cfg.velocity = r.velocity

			self.undo_buff.add_state()
			if self.edit:
				self.redraw(self.edit[1])
			else:
				self.redraw(self.select_start[1], self.select_end[1])
			return True
			
		if sel and alt and event.keyval == 65364:	# alt+down on selection
			for r in sel:
				if r.type:
					r.velocity = max(r.velocity - 1, 0)
					mod.cfg.velocity = r.velocity
			
			self.undo_buff.add_state()
			if self.edit:
				self.redraw(self.edit[1])
			else:
				self.redraw(self.select_start[1], self.select_end[1])
			return True
			
		if sel and alt and event.keyval == 65366:	# alt+page down on selection
			for r in sel:
				if r.type:
					r.velocity = max(r.velocity - 10, 0)
					mod.cfg.velocity = r.velocity
			
			self.undo_buff.add_state()
			if self.edit:
				self.redraw(self.edit[1])
			else:
				self.redraw(self.select_start[1], self.select_end[1])
			return True			
			
		if event.keyval == 65364:						# down
			if self.edit:
				if shift:
					self.select_start = self.edit
					self.select_end = self.edit[0], min(self.edit[1] + 1, self.trk.nrows -1)
					self.edit = None
					self.redraw(self.select_start[1], self.select_end[1])
					return True
				else:
					self.edit = self.edit[0], self.edit[1] + 1
					if self.edit[1] >= self.trk.nrows:
						self.edit = self.edit[0], 0

					self.redraw(self.edit[1])
					redr = True
			else:
				if shift:
					oldy = self.select_start[1]
					oldyy = self.select_end[1]
					self.select_end = self.select_end[0], min(self.select_end[1] + 1, self.trk.nrows - 1)
					self.redraw(oldy, oldyy)
					self.redraw(self.select_start[1], self.select_end[1])
					return True
				else:
					if self.select_start:
						old = self.select_start[1], self.select_end[1]
						self.edit = self.select_end[0], min(self.select_end[1] + 1, self.trk.nrows - 1)
						self.select_start = None
						self.select_end = None
						self.redraw(*(old))
						self.redraw(self.edit[1])
					return True
			
		if event.keyval == 65362:			# up
			if self.edit:
				if shift:
					self.select_start = self.edit
					self.select_end = self.edit[0], max(self.edit[1] - 1, 0)
					self.edit = None
					self.redraw(self.select_start[1], self.select_end[1])
					return True
				else:
					self.edit = self.edit[0], self.edit[1] - 1
					if self.edit[1] < 0:
						self.edit = self.edit[0], self.trk.nrows - 1

					self.redraw(self.edit[1])
					redr = True
			else:
				if shift:
					oldy = self.select_start[1]
					oldyy = self.select_end[1]
					self.select_end = self.select_end[0], max(self.select_end[1] - 1, 0)
					self.redraw(oldy, oldyy)
					self.redraw(self.select_start[1], self.select_end[1])
					return True
				else:
					if self.select_start:
						old = self.select_start[1], self.select_end[1]
						self.edit = self.select_end[0], max(self.select_end[1] - 1, 0)
						self.select_start = None
						self.select_end = None
						self.redraw(*(old))
						self.redraw(self.edit[1])
					return True
		
		if event.keyval == 65363:			# right
			if not shift:
				if self.select_start:
					old = self.select_start[1], self.select_end[1]
					self.edit = self.select_end
					self.select_start = None
					self.select_end = None
					self.redraw(*(old))
				
				if self.edit:
					self.go_right()
				return True

			if shift:
				if self.edit:
					self.select_start = self.edit
					self.select_end = min(self.edit[0] + 1, len(self.trk) - 1), self.edit[1]
					self.edit = None
					self.redraw(self.select_start[1], self.select_end[1])
					return True
				
				if self.select_end:
					self.select_end = min(self.select_end[0] + 1, len(self.trk) - 1), self.select_end[1]
					self.redraw(self.select_start[1], self.select_end[1])
					return True
			
		if event.keyval == 65361:			# left
			if not shift:
				if self.select_start:
					old = self.select_start[1], self.select_end[1]
					self.edit = self.select_end
					self.select_start = None
					self.select_end = None
					self.redraw(*(old))
				
				if self.edit:
					self.go_left()
				return True

			if shift:
				if self.edit:
					self.select_start = self.edit
					self.select_end = max(self.edit[0] - 1, 0), self.edit[1]
					self.edit = None
					self.redraw(self.select_start[1], self.select_end[1])
					return True
				
				if self.select_end:
					self.select_end = max(self.select_end[0] - 1, 0), self.select_end[1]
					self.redraw(self.select_start[1], self.select_end[1])
					return True

		if event.keyval == 65366:			# page-down
			if not shift:
				old = None
				if self.edit:
					old = self.edit[1], self.edit[1]
					self.edit = self.edit[0], self.edit[1] + 1
					
				elif self.select_end:
					old = self.select_start[1], self.select_end[1]
					self.edit = self.select_end[0], self.select_end[1] + 1
					self.select_end = None
					self.select_start = None

				if not self.edit:
					return True
					
				while not self.edit[1] % mod.cfg.highlight == 0:
					self.edit = self.edit[0], self.edit[1] + 1
			
				if self.edit[1] >= self.trk.nrows:
					self.edit = self.edit[0], self.trk.nrows - 1
			
				if old:
					self.redraw(*(old))
					
				self.redraw(self.edit[1])
				return True

			if shift:
				if self.edit:
					self.select_start = self.edit
					self.select_end = self.edit[0], self.edit[1]
					self.edit = None
			
				if self.select_end:
					old = self.select_start[1], self.select_end[1]
					self.select_end = self.select_end[0], self.select_end[1] + 1
					
					while not self.select_end[1] % mod.cfg.highlight == 0:
						self.select_end = self.select_end[0], self.select_end[1] + 1
					
					self.select_end = self.select_end[0], min(self.select_end[1], self.trk.nrows - 1)
					
					self.redraw(*(old))
					self.redraw(self.select_start[1], self.select_end[1])
				return True
				
		if event.keyval == 65365:			# page-up
			if not shift:
				old = None
				if self.edit:
					old = self.edit[1], self.edit[1]
					self.edit = self.edit[0], self.edit[1] - 1
					
				elif self.select_end:
					old = self.select_start[1], self.select_end[1]
					self.edit = self.select_end[0], self.select_end[1] - 1
					self.select_end = None
					self.select_start = None

				if not self.edit:
					return True
					
				while not self.edit[1] % mod.cfg.highlight == 0:
					self.edit = self.edit[0], self.edit[1] - 1
			
				self.edit = self.edit[0], max(self.edit[1], 0)
			
				if old:
					self.redraw(*(old))
					
				self.redraw(self.edit[1])
				return True

			if shift:
				if self.edit:
					self.select_start = self.edit
					self.select_end = self.edit[0], self.edit[1]
					self.edit = None
			
				if self.select_end:
					old = self.select_start[1], self.select_end[1]
					self.select_end = self.select_end[0], self.select_end[1] - 1
					
					while not self.select_end[1] % mod.cfg.highlight == 0:
						self.select_end = self.select_end[0], self.select_end[1] - 1
					
					self.select_end = self.select_end[0], max(self.select_end[1], 0)
					self.redraw(*(old))
					self.redraw(self.select_start[1], self.select_end[1])
				return True
		
		if event.keyval == 65360:			# home
			if not shift:
				if self.edit:
					old = self.edit[1], self.edit[1]
					
				if self.select_start:
					old = self.select_start[1], self.select_end[1]
					self.edit = self.select_end
					self.select_start = None
					self.select_end = None
				
				self.edit = self.edit[0], 0
				self.redraw(*(old))
				self.redraw(self.edit[1])
				return True
			
			if shift:
				if self.edit:
					self.select_start = self.edit
					self.select_end = self.edit[0], 0
					self.edit = None
				
				if self.select_end:
					old = self.select_start[1], self.select_end[1]
					self.select_end = self.select_end[0], 0
					self.redraw(*(old))
					self.redraw(self.select_start[1], self.select_end[1])
				return True
		
		if event.keyval == 65367:			# end
			if not shift:
				if self.edit:
					old = self.edit[1], self.edit[1]
					
				if self.select_start:
					old = self.select_start[1], self.select_end[1]
					self.edit = self.select_end
					self.select_start = None
					self.select_end = None
				
				self.edit = self.edit[0], self.trk.nrows - 1
				self.redraw(*(old))
				self.redraw(self.edit[1])
				return True
			
			if shift:
				if self.edit:
					self.select_start = self.edit
					self.select_end = self.edit[0], self.trk.nrows - 1
					self.edit = None
				
				if self.select_end:
					old = self.select_start[1], self.select_end[1]
					self.select_end = self.select_end[0], self.trk.nrows - 1
					self.redraw(*(old))
					self.redraw(self.select_start[1], self.select_end[1])
				return True
			
		if redr and old:
			self.redraw(old[1])
			return True

		if event.keyval == 65535:			# del
			sel = self.selection()
			if sel:
				for r in sel:
					r.clear()
			
				self.redraw()
				return True

			if not self.edit:
				return True
			
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
				self.edit = self.edit[0], self.edit[1] + mod.cfg.skip
				if self.edit[1] >= self.trk.nrows:
					self.edit = self.edit[0], self.trk.nrows - 1
					
				self.redraw(self.edit[1])
				self.redraw(old)

			self.undo_buff.add_state()
			return True
		
		if not self.edit:
			return False

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
		
		if event.keyval == 65056:			# shift-tab
			self.go_left(True)
			return True

		if event.keyval == 65289:			# tab
			self.go_right(True)
			return True
		
		if event.keyval == 92:				# | note_off
			self.trk[self.edit[0]][self.edit[1]].clear()
			self.trk[self.edit[0]][self.edit[1]].type = 2
			
			old = self.edit[1]
			self.edit = self.edit[0], self.edit[1] + mod.cfg.skip

			if self.edit[1] >= self.trk.nrows:
				self.edit = self.edit[0], self.edit[1] - self.trk.nrows
			
			while self.edit[1] < 0:
				self.edit = self.edit[0], self.edit[1] + self.trk.nrows
					
			self.redraw(self.edit[1])
			self.redraw(old)
			
			self.undo_buff.add_state()
		
		return False

	def on_key_release(self, widget, event):
		if not self.trk:
			return
		
		#print("key : %d" % (event.keyval))
		note = self.pmp.key2note(event.keyval, True)
		return False
