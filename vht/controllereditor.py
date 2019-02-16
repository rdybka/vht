import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk
import cairo
import math
import string

from vht import cfg, mod
from vht.controllerundobuffer import ControllerUndoBuffer

class ControllerEditor():
	clipboard = []
	doodle_clipboard = []

	def __init__(self, tv, ctrlnum = 0):
		self.tv = tv
		self.trk = tv.trk

		self.x_from = 0
		self.l_x_from = 0
		self.x_to = 0
		self.txt_width = 0
		self.width = 64
		self.ctrlnum = ctrlnum
		self.ctrlrows = self.trk.ctrl[self.ctrlnum]
		self.midi_ctrlnum = self.trk.ctrls[self.ctrlnum]
		self.deleting = False
		self.drawing = False
		self.moving = False
		self.selecting = False
		self.last_selected = -1
		self.moving_selection_start = -1
		self.ignore_x = False
		self.last_r = -1
		self.last_x = -1
		self.snap = False
		self.env = None
		self.env_cr = None
		self.env_sf = None
		self.ctrl_cr = None
		self.ctrl_sf = None
		self.active_node = -1
		self.active_row = -1
		self.node_size = 0

		self.txt_height = 0
		self.txt_x = 0
		self.zero_pattern_surface = None
		self.empty_pattern_surface = None
		self.zero_pattern_highlight = -1

		self.edit = -1
		self.last_keyboard_edit = -1
		self.selection = None
		self.moving_rows = False
		self.drag = False
		self.dragged = False
		self.drag_content = None
		self.drag_static = None
		self.drag_selection_offset = -1
		self.drag_start = -1

		self.undo_buff = ControllerUndoBuffer(self.trk, self.ctrlnum)

	def precalc(self, cr, x_from):
		(x, y, width, height, dx, dy) = cr.text_extents("0")
		self.width = cfg.controllereditor_char_width * width
		w1 = width
		(x, y, width, height, dx, dy) = cr.text_extents("0000")
		self.txt_width = width
		self.width = self.width + self.txt_width
		reconf = False
		if self.x_from != x_from:
			reconf = True
		self.x_from = x_from
		self.x_to = x_from + self.width - w1

		if reconf:
			self.configure()

	def configure(self):
		if self.x_to == 0:
			return

		if not self.trk.ctrls:
			return

		recr_cr = False

		if self.l_x_from != self.x_from:
			self.l_x_from = self.x_from
			recr_cr = True

		if self.env_cr:
			if self.env_cr.get_target().get_width() != self.x_to - self.x_from:
				recr_cr = True
			if self.env_cr.get_target().get_height() != self.tv._back_surface.get_height():
				recr_cr = True

		if not self.zero_pattern_surface:
			recr_cr = True

		if self.zero_pattern_highlight != cfg.highlight:
			 self.zero_pattern_highlight = cfg.highlight
			 recr_cr = True

		if recr_cr:
			if self.env_sf:
				self.env_sf.finish()

			if self.ctrl_sf:
				self.ctrl_sf.finish()

			self.env_sf = self.tv._back_surface.create_similar(cairo.CONTENT_COLOR_ALPHA, int(self.x_to - self.x_from), self.tv._back_surface.get_height())
			self.env_cr = cairo.Context(self.env_sf)

			self.env_cr.select_font_face(cfg.seq_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
			self.env_cr.set_font_size(cfg.seq_font_size)

			self.ctrl_sf = self.tv._back_surface.create_similar(cairo.CONTENT_COLOR_ALPHA, 128, self.trk.nrows * self.trk.ctrlpr)
			self.ctrl_cr = cairo.Context(self.env_sf)

			# zero pattern
			if self.zero_pattern_surface:
				self.zero_pattern_surface.finish()

			if self.empty_pattern_surface:
				self.empty_pattern_surface.finish()

			self.zero_pattern_surface = self.tv._back_surface.create_similar(cairo.CONTENT_COLOR_ALPHA, int(self.x_to - self.x_from), round(self.tv.txt_height * 2))
			cr = cairo.Context(self.zero_pattern_surface)

			cr.set_source_rgb(*(col * cfg.intensity_background for col in cfg.colour))
			cr.rectangle(0, 0, self.width, self.tv.txt_height)
			cr.fill()
			cr.set_source_rgb(*(col * cfg.intensity_background * cfg.even_highlight for col in cfg.colour))
			cr.rectangle(0, self.tv.txt_height, self.width, self.tv.txt_height)
			cr.fill()

			self.zero_pattern = cairo.SurfacePattern(self.zero_pattern_surface)
			self.zero_pattern.set_extend(cairo.Extend.REPEAT)
			matrix = cairo.Matrix()
			# because rowheight is float
			matrix.scale(1.0, round(self.tv.txt_height * 2) / (self.tv.txt_height * 2))
			self.zero_pattern.set_matrix(matrix)

			# empty pattern
			empl = self.zero_pattern_highlight
			empl *= 1 + empl % 2 						# oh yeah

			self.empty_pattern_surface = self.tv._back_surface.create_similar(cairo.CONTENT_COLOR_ALPHA, int(self.x_to - self.x_from), round(self.tv.txt_height * empl))
			cr = cairo.Context(self.empty_pattern_surface)

			cr.select_font_face(cfg.seq_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
			cr.set_font_size(cfg.seq_font_size)

			(x, y, width, height, dx, dy) = cr.text_extents("0000")

			self.txt_height = height
			self.txt_x = x

			for r in range(empl):
				even_high = cfg.even_highlight
				if not r % 2:
					even_high = 1.0

				cr.set_source_rgb(*(col * cfg.intensity_background * even_high for col in cfg.colour))
				cr.rectangle(0, r * self.tv.txt_height, self.width, self.tv.txt_height)
				cr.fill()

				if self.zero_pattern_highlight > 1 and (r) % cfg.highlight == 0:
					cr.set_source_rgb(*(col * cfg.intensity_txt_highlight for col in cfg.colour))
				else:
					cr.set_source_rgb(*(col * cfg.intensity_txt for col in cfg.colour))

				yy = (r + 1) * self.tv.txt_height - ((self.tv.txt_height - height) / 2.0)
				cr.move_to(x, yy)
				cr.show_text("---")

			self.empty_pattern = cairo.SurfacePattern(self.empty_pattern_surface)
			self.empty_pattern.set_extend(cairo.Extend.REPEAT)
			matrix = cairo.Matrix()
			matrix.translate(-self.x_from, 0)
			# because rowheight is float
			matrix.scale(1.0, round(self.tv.txt_height * self.zero_pattern_highlight) / (self.tv.txt_height * self.zero_pattern_highlight))
			self.empty_pattern.set_matrix(matrix)

			self.redraw_env()

	def redraw_env(self):
		cr = self.env_cr

		node_size = 0

		cr.set_operator(cairo.Operator.CLEAR)
		self.env_cr.paint()
		cr.set_operator(cairo.Operator.OVER)

		self.env = self.env = self.trk.get_envelope(self.ctrlnum)

		if self.env:
			if len(self.env):
				cr.set_source_rgba(*(col * cfg.intensity_lines * 1 for col in cfg.star_colour), 1)
				(x, y, width, height, dx, dy) = cr.text_extents("*")
				node_size = dx
				self.node_size = dx# / 2

			# nodes
			for n, node in enumerate(self.env):
				cr.set_source_rgba(*(col * cfg.intensity_lines * 2 for col in cfg.star_colour), 1)

				xw = self.x_to - (self.x_from + self.txt_width)
				x0 = xw / 2

				xx = (node["x"]) - 64
				xx = xx * ((xw / 2) / 64)

				if self.active_node == n:
					size_div = 2
				else:
					size_div = 3

				if self.active_node == n:
					cr.set_source_rgba(*(col * cfg.intensity_lines * 4 for col in cfg.star_colour), 1)

				cr.arc((x0 + xx), node["y"] * self.tv.txt_height - ((node_size / size_div) / 4), node_size / size_div, 0, 2 * math.pi)

				if node["l"]:
					cr.fill()
				else:
					cr.stroke()

			self.tv.queue_draw()

	def draw(self, cr, r):
		if not cr:
			cr = self.tv._back_context

		if not cr:
			return

		if not self.empty_pattern_surface:
			self.configure()

		yh = self.tv.txt_height

		xw = self.x_to - (self.x_from + self.txt_width)
		x0 = self.x_from + self.txt_width + (xw / 2)

		row = self.ctrlrows[r]

		select = False
		empty = False
		hover = False

		if self.tv.hover and r == self.tv.hover[1]:
			hover = True

		if self.selection:
			if self.selection[1] - self.selection[0] > 0:
				if r >= self.selection[0] and r<= self.selection[1]:
					select = True
					cr.set_source_rgb(*(col * cfg.intensity_select for col in cfg.colour))

		if self.edit == r:
			if mod.record == 0:
				if not select:
					cr.set_source_rgb(*(cfg.record_colour))
					select = True

		if row.velocity == -1 or empty:		# empty row
			if select:
				cr.set_source(self.zero_pattern)
				cr.rectangle(self.x_from, r * self.tv.txt_height, self.x_to - self.x_from, yh)
				cr.fill()

				if self.edit == r and not self.selection:
					cr.set_source_rgb(*(cfg.record_colour))
					cr.rectangle(self.x_from + self.txt_x, (r * self.tv.txt_height) + yh * .1, (self.x_to - self.x_from) - (self.txt_x * 2), yh * .8)
				else:
					cr.set_source_rgb(*(col * cfg.intensity_select for col in cfg.colour))
					cr.rectangle(self.x_from, r * self.tv.txt_height, self.x_to - self.x_from, yh)

				cr.fill()
			else:
				cr.set_source(self.empty_pattern)
				cr.rectangle(self.x_from, r * self.tv.txt_height, self.x_to - self.x_from, yh)
				cr.fill()

			if select or self.edit == r or hover:
				if self.zero_pattern_highlight > 1 and (r) % self.zero_pattern_highlight == 0:
					cr.set_source_rgb(*(col * cfg.intensity_txt_highlight for col in cfg.colour))
				else:
					cr.set_source_rgb(*(col * cfg.intensity_txt for col in cfg.colour))

				yy = (r + 1) * self.tv.txt_height - ((self.tv.txt_height - self.txt_height) / 2.0)
				cr.move_to(self.x_from + self.txt_x, yy)

				if hover and not select:
					cr.set_source_rgb(*(col * cfg.intensity_txt_highlight * 1.2 for col in cfg.colour))
				else:
					cr.set_source_rgb(*(col * cfg.intensity_background for col in cfg.colour))
				cr.show_text("---")
		else:
			cr.set_source(self.zero_pattern)
			cr.rectangle(self.x_from, r * self.tv.txt_height, self.x_to - self.x_from, yh)
			cr.fill()

			if select:
				if self.edit == r and not self.selection:
					cr.set_source_rgb(*(cfg.record_colour))
					cr.rectangle(self.x_from + self.txt_x, (r * self.tv.txt_height) + yh * .1, (self.x_to - self.x_from) - (self.txt_x * 2), yh * .8)
				else:
					cr.set_source_rgb(*(col * cfg.intensity_select for col in cfg.colour))
					cr.rectangle(self.x_from, r * self.tv.txt_height, self.x_to - self.x_from, yh)

				cr.fill()

			if self.zero_pattern_highlight > 1 and (r) % self.zero_pattern_highlight == 0:
				cr.set_source_rgb(*(col * cfg.intensity_txt_highlight for col in cfg.colour))
			else:
				cr.set_source_rgb(*(col * cfg.intensity_txt for col in cfg.colour))

			if select:
				cr.set_source_rgb(*(col * cfg.intensity_background for col in cfg.colour))

			if hover and not select:
				cr.set_source_rgb(*(col * cfg.intensity_txt_highlight * 1.2 for col in cfg.colour))

			lnkchar = " "
			if row.linked:
				lnkchar = "L"

			yy = (r + 1) * self.tv.txt_height - ((self.tv.txt_height - self.txt_height) / 2.0)
			cr.move_to(self.x_from + self.txt_x, yy)
			cr.show_text("%03d%c" % (row.velocity, lnkchar))

		cr.set_line_width(1.0)
		cr.set_source_rgba(*(col * cfg.intensity_txt for col in cfg.colour), .2)
		cr.rectangle(self.x_from + self.txt_width, r * self.tv.txt_height, xw, yh)
		cr.fill()

		if self.ctrlnum == None:
			cr.set_source_rgba(*(col * cfg.intensity_txt for col in cfg.colour), .3)
			cr.move_to(x0, r * yh)
			cr.line_to(x0, (r + 1) * yh)
			cr.stroke()
			return

		ctrl = self.trk.get_ctrl_rec(self.ctrlnum, r)
		yp = yh / len(ctrl)
		y0 = r * yh

		cr.set_source_rgba(*(col * cfg.intensity_txt for col in cfg.record_colour), .7)
		for v in ctrl:
			if self.ctrlnum == 0:
				xx = (v / 127) - 64
			else:
				xx = v - 64

			xx = xx * ((xw / 2) / 64)

			if v == -1:
				xx = 0

			if x0 + xx > self.x_to:
				xx = self.x_to - x0

			if self.ctrlnum == 0:
				cr.rectangle(x0, y0, xx, yp)
			else:
				if v != -1:
					cr.rectangle(self.x_from + self.txt_width, y0, (xw / 2) + xx, yp)

			cr.fill()

			y0 = y0 + yp

		ctrl = self.trk.get_ctrl_env(self.ctrlnum, r)
		yp = yh / len(ctrl)
		y0 = r * yh

		cr.set_source_rgba(*(col * cfg.intensity_txt for col in cfg.colour), .4)
		for v in ctrl:
			if self.ctrlnum == 0:
				xx = (v / 127) - 64
			else:
				xx = v - 64

			xx = xx * ((xw / 2) / 64)

			if v == -1:
				xx = 0

			if x0 + xx > self.x_to:
				xx = self.x_to - x0

			if self.ctrlnum == 0:
				cr.rectangle(x0, y0, xx, yp)
			else:
				if v != -1:
					cr.rectangle(self.x_from + self.txt_width, y0, (xw / 2) + xx, yp)

			y0 = y0 + yp

		cr.fill()

		cr.set_source_rgba(*(col * cfg.intensity_lines for col in cfg.colour), 1)
		cr.move_to(x0, r * yh)
		cr.line_to(x0, (r + 1) * yh)
		cr.stroke()

		cr.set_source_rgba(*(col * cfg.intensity_lines for col in cfg.colour), 1)
		cr.move_to(self.x_from, r * yh)
		cr.line_to(self.x_from, (r + 1) * yh)
		cr.stroke()

		cr.move_to(self.x_to, r * yh)
		cr.line_to(self.x_to, (r + 1) * yh)
		cr.stroke()

		if self.env_sf:
			cr.set_source_surface(self.env_sf, self.x_from + self.txt_width, 0)
			cr.rectangle(self.x_from + self.txt_width, r * yh, xw, yh)
			cr.fill()

	def on_key_press(self, widget, event):
		shift = False
		ctrl = False
		alt = False

		if event.state:
			if event.state & Gdk.ModifierType.SHIFT_MASK:
				shift = True

			if event.state & Gdk.ModifierType.CONTROL_MASK:
				ctrl = True

			if event.state & Gdk.ModifierType.MOD1_MASK:
				alt = True

		if shift and self.selection:
			self.selecting = True

		handled = False

		if not shift and not ctrl and not alt:
			if self.tv.pmp.key2ctrl(Gdk.keyval_to_lower(event.keyval), self.midi_ctrlnum):
				handled = True

		if cfg.key["node_snap"].matches(event):
			self.snap = True

		if self.selection:
			if cfg.key["delete"].matches(event):
				for r in range((self.selection[1] - self.selection[0]) + 1):
					self.trk.ctrl[self.ctrlnum][r + self.selection[0]].clear()

				self.trk.ctrl[self.ctrlnum].refresh()
				handled = True

		# link / delete / value
		sel = False
		if self.selection:
			if (self.selection[1] - self.selection[0]) > 0:
				sel = True

		key = Gdk.keyval_name(Gdk.keyval_to_lower(event.keyval))
		if self.edit != -1 and not sel:
			if cfg.key["link"].matches(event):
				l = self.trk.ctrl[self.ctrlnum][self.edit].linked
				if l == 0:
					l = 1
				else:
					l = 0
				self.trk.ctrl[self.ctrlnum][self.edit].linked = l
				self.edit += cfg.skip
				if self.edit > self.trk.nrows - 1:
					self.edit -= self.trk.nrows
				if self.edit < 0:
					self.edit += self.trk.nrows
				handled = True

			if cfg.key["delete"].matches(event):
				self.trk.ctrl[self.ctrlnum][self.edit].clear()
				self.edit = self.edit + cfg.skip
				if self.edit >= self.trk.nrows:
					self.edit = 0
				handled = True

			if not shift and not ctrl and not alt:
				f = cfg.velocity_keys.find(key)
				val = -1
				if f > -1:
					val = int(f * (127 / (len(cfg.velocity_keys) - 1)))

					if f == 0:
						val = 0

					if f == len(cfg.velocity_keys) - 1:
						val = 127

					if f == math.floor(len(cfg.velocity_keys) / 2):
						val = 64

					if self.trk.ctrl[self.ctrlnum][self.edit].velocity == -1:
						self.trk.ctrl[self.ctrlnum][self.edit].linked = 0
						self.trk.ctrl[self.ctrlnum][self.edit].anchor = 0
						self.trk.ctrl[self.ctrlnum][self.edit].smooth = 0

					self.trk.ctrl[self.ctrlnum][self.edit].velocity = val
					self.edit += cfg.skip
					if self.edit > self.trk.nrows - 1:
						self.edit -= self.trk.nrows
					if self.edit < 0:
						self.edit += self.trk.nrows

					handled = True

			if key in string.digits:
				val = self.trk.ctrl[self.ctrlnum][self.edit].velocity
				self.undo_buff.add_state()

				if self.edit != self.last_keyboard_edit:
					val = 0
					self.last_keyboard_edit = self.edit

				if val <= 0:
					val = int(key)
				else:
					s = "%d%d" % (val, int(key))
					val = int(s[-3:])
					if val > 127:
						val = int(s[-1:])

				self.trk.ctrl[self.ctrlnum][self.edit].velocity = val
				handled = True

		if cfg.key["undo"].matches(event) and not self.moving and not self.drag:
			self.undo_buff.restore()
			handled = True

		if cfg.key["select_all"].matches(event):
			if self.selection and self.selection[0] == 0 and self.selection[1] == self.trk.nrows -1:
				self.selection = None
				self.edit = -1
				self.tv.redraw()
				return True

			self.tv.leave_all()
			self.selection = (0, self.trk.nrows -1)
			self.edit = self.selection[1]
			handled = True

		if cfg.key["doodle_cut"].matches(event):
			if not self.selection and self.edit == -1:
				return False

			s = max(self.edit, -1)
			e = s
			if self.selection:
				s = self.selection[0]
				e = self.selection[1]

			if s == -1:
				return False

			self.to_clipboard(True)

			for r in range(s, min(e + 1, self.trk.nrows)):
				offs = self.trk.ctrlpr * r
				for rr in range(self.trk.ctrlpr):
					self.trk.set_ctrl(self.ctrlnum, offs + rr, -1)

			handled = True

		if cfg.key["cut"].matches(event):
			if not self.selection and self.edit == -1:
				return False

			s = max(self.edit, -1)
			e = s
			if self.selection:
				s = self.selection[0]
				e = self.selection[1]

			if s == -1:
				return False

			self.to_clipboard()

			for r in range(s, min(e + 1, self.trk.nrows)):
				self.trk.ctrl[self.ctrlnum][r].clear()

			handled = True

		if cfg.key["doodle_delete"].matches(event):
			if not self.selection and self.edit == -1:
				return False

			s = max(self.edit, -1)
			e = s
			if self.selection:
				s = self.selection[0]
				e = self.selection[1]

			if s == -1:
				return False

			for r in range(s, min(e + 1, self.trk.nrows)):
				offs = self.trk.ctrlpr * r
				for rr in range(self.trk.ctrlpr):
					self.trk.set_ctrl(self.ctrlnum, offs + rr, -1)

			return True

		if cfg.key["doodle_copy"].matches(event):
			if not self.selection and self.edit == -1:
				return False

			self.to_clipboard(True)
			return True

		if cfg.key["copy"].matches(event):
			if not self.selection and self.edit == -1:
				return False

			self.to_clipboard()
			return True

		if cfg.key["doodle_paste"].matches(event):
			if not self.selection and self.edit == -1:
				return False

			self.from_clipboard(True)
			handled = True

		if cfg.key["doodle_render"].matches(event):
			if not self.selection and self.edit == -1:
				return False

			self.render_doodles()
			handled = True

		if cfg.key["paste"].matches(event):
			if not self.selection and self.edit == -1:
				return False

			self.from_clipboard()
			handled = True

		if handled:
			self.trk.ctrl[self.ctrlnum].refresh()
			self.env = self.trk.get_envelope(self.ctrlnum)
			self.redraw_env()
			self.tv.redraw(controller = self.ctrlnum)
			self.undo_buff.add_state()
			return True

		if self.edit != -1:
			olded = self.edit
			if event.keyval == 65364:						# down
				self.edit = self.edit + 1
				if self.edit >= self.trk.nrows:
					self.edit = 0

			if event.keyval == 65362:						# up
				self.edit = self.edit - 1
				if self.edit == -1:
					self.edit = self.trk.nrows - 1

			if event.keyval == 65363:						# right
				pass

			if event.keyval == 65361:						# left
				pass

			if event.keyval == 65360:						# home
				self.edit = 0

			if event.keyval == 65367:						# end
				self.edit = self.trk.nrows -1

			if event.keyval == 65365:						# page-up
				self.edit = self.edit - 1
				while not self.edit % cfg.highlight == 0:
					self.edit = self.edit - 1
				if self.edit < 0:
					self.edit = 0

			if event.keyval == 65366:						# page-down
				self.edit = self.edit + 1
				while not self.edit % cfg.highlight == 0:
					self.edit = self.edit + 1
				if self.edit >= self.trk.nrows:
					self.edit = self.trk.nrows -1

			if event.keyval == 65056:						# shift-tab
				pass

			if event.keyval == 65289:						# tab
				pass

			if self.edit != olded:
				oldsel = self.selection
				self.last_keyboard_edit = -1

				if not shift:
					if self.selection: 						# remove selection?
						self.selection = None
						self.tv.redraw(oldsel[0], oldsel[1], controller = self.ctrlnum)
				else: 										# expand selection
					if self.edit > olded: 					# going down
						if self.selection:
							if self.edit > self.selection[1]:
								if olded < self.selection[1]: 	# jump up and get down
									self.selection = self.selection[1], self.edit
								else:
									self.selection = self.selection[0], self.edit
							else:
								if (self.edit <= self.selection[1] and
								self.edit > self.selection[0]):
									self.selection = self.edit, self.selection[1]
						else: # no selection
							self.selection = olded, self.edit
							oldsel = self.selection
					else: 									# going up
						if self.selection:
							if self.edit < self.selection[0]:
								if olded > self.selection[0]: 	# jump around, jump around
									self.selection = self.edit, self.selection[0]
								else:
									self.selection = self.edit, self.selection[1]
							else:
								if (self.edit >= self.selection[0] and
								self.edit < self.selection[1]):
									self.selection = self.selection[0], self.edit
						else: # no selection
							self.selection = self.edit, olded
							oldsel = self.selection

				self.tv.recalc_edit(self.tv)
				if self.selection:
					updsel = min(oldsel[0], self.selection[0]), max(oldsel[1], self.selection[1])
					self.tv.redraw(updsel[0], updsel[1], controller = self.ctrlnum)
				else:
					self.tv.redraw(olded, controller = self.ctrlnum)
					self.tv.redraw(self.edit, controller = self.ctrlnum)
				return True

		return False

	def on_key_release(self, widget, event):
		handled = False

		if self.tv.pmp.key2ctrl(Gdk.keyval_to_lower(event.keyval), self.midi_ctrlnum, True):
			handled = True

		if event.state:
			if event.state & Gdk.ModifierType.SHIFT_MASK:
				self.selecting = False

		if cfg.key["node_snap"].matches(event):
			self.snap = False

		return handled

	def on_button_press(self, widget, event):
		if event.x < self.x_from or event.x > self.x_to:
			return

		if event.button == cfg.select_button:
			if not self.tv.keyboard_focus:
					self.tv.keyboard_focus = self
					self.tv.parent.prop_view.redraw()
			else:
				if self.tv.keyboard_focus != self or mod.active_track != self.tv:
					self.tv.keyboard_focus = self
					self.tv.leave_all()
					self.tv.parent.change_active_track(self.tv)
					self.tv.parent.prop_view.redraw()


		self.ignore_x = False

		# handle clicks in left pane
		if event.x < self.x_from + self.txt_width:
			self.ignore_x = True
			shift = False
			if event.state & Gdk.ModifierType.SHIFT_MASK:
				shift = True

			r = min(int(event.y / self.tv.txt_height), self.trk.nrows - 1)

			right = False
			if event.button == cfg.delete_button:
				right = True

			if not right and not shift:
				# move selection?
				if self.selection:
					if r >= self.selection[0] and r <= self.selection[1]:
						self.edit = r
						self.drag = True
						self.dragged = False
						self.drag_content = []
						self.drag_static = []
						self.drag_selection_offset = r - self.selection[0]
						self.drag_start = self.selection[0]

						for rr, row in enumerate(self.trk.ctrl[self.ctrlnum]):
							rd = row.dummy()

							if rr >= self.selection[0] and rr <= self.selection[1]:
								self.drag_content.append(row)
								rd.clear()

							self.drag_static.append(rd)
						return

				if self.edit != r:
					self.tv.leave_all()
					self.tv.set_opacity(1)
					self.edit = r
					self.selection = None
					self.last_keyboard_edit = -1
					self.tv.recalc_edit(self.tv)

				self.active_row = r
				self.last_selected = r

				if self.trk.ctrl[self.ctrlnum][int(r)].velocity is -1:
					self.selecting = True
				else:
					self.moving = True

				self.tv.redraw(controller = self.ctrlnum)

			# expand selection
			if shift:
				if r > self.last_selected:
					self.selection = (self.last_selected, r)

				if r < self.last_selected:
					self.selection = (r, self.last_selected)

				self.selecting = True
				self.tv.redraw(controller = self.ctrlnum)

			# delete row or clear selection
			if right:
				if self.trk.ctrl[self.ctrlnum][int(r)].velocity == -1:
					self.tv.leave_all()
					self.selection = None
					self.edit = -1
					self.tv.redraw(controller = self.ctrlnum)
				else:
					self.trk.ctrl[self.ctrlnum][int(r)].clear()
					self.trk.ctrl[self.ctrlnum].refresh()
					self.env = self.trk.get_envelope(self.ctrlnum)
					self.redraw_env()
					self.tv.redraw(controller = self.ctrlnum)
			return

		# right pane
		ctrl = False
		if event.state & Gdk.ModifierType.CONTROL_MASK:
			ctrl = True

		if self.active_node != -1:
			node = self.env[self.active_node]

			if event.button == cfg.delete_button:
				r = int(node["y"])

				self.trk.ctrl[self.ctrlnum][r].clear()
				self.trk.ctrl[self.ctrlnum].refresh()
				self.active_node = -1
				self.env = self.trk.get_envelope(self.ctrlnum)
				self.redraw_env()
				self.tv.redraw(controller = self.ctrlnum)
				return True

			if event.button == cfg.select_button:
				if event.type == Gdk.EventType._2BUTTON_PRESS or event.type == Gdk.EventType._3BUTTON_PRESS:
					r = int(node["y"])

					l = node["l"]

					if l == 0:
						l = 1
					else:
						l = 0

					self.trk.ctrl[self.ctrlnum][r].linked = l

					self.env = self.trk.get_envelope(self.ctrlnum)
					self.on_motion(widget, event)
					self.redraw_env()
					self.edit = -1
					self.tv.redraw(controller = self.ctrlnum)

					return True
				else:
					self.tv.leave_all()
					self.moving = True

				return True

		if event.button == cfg.delete_button:
			self.deleting = True
			self.last_r = -1
			self.last_x = -1
			self.on_motion(widget, event)

		if not ctrl and event.button == cfg.select_button:
			self.drawing = True
			self.last_r = -1
			self.last_x = -1
			self.on_motion(widget, event)

		# add node
		if ctrl:
			xw = self.x_to - (self.x_from + self.txt_width)
			x0 = self.x_from + (xw / 2)
			v = max(min(((event.x - (self.x_from + self.txt_width)) / xw) * 127, 127), 0)

			r = event.y / self.tv.txt_height

			if self.trk.ctrl[self.ctrlnum][int(r)].velocity != -1:
				return

			empty = True
			for row in self.trk.ctrl[self.ctrlnum]:
				if row.velocity != -1:
					empty = False

			self.trk.ctrl[self.ctrlnum][int(r)].velocity = v
			self.trk.ctrl[self.ctrlnum][int(r)].smooth = 0

			if empty:
				self.trk.ctrl[self.ctrlnum][int(r)].linked = 0
			else:
				self.trk.ctrl[self.ctrlnum][int(r)].linked = 1

			anchor = 0
			if r - int(r) > .5:
				anchor = 1

			self.trk.ctrl[self.ctrlnum][int(r)].anchor = anchor

			self.trk.ctrl[self.ctrlnum].refresh()
			self.env = self.trk.get_envelope(self.ctrlnum)

			self.on_motion(widget, event)
			self.moving = True
			self.redraw_env()
			self.tv.redraw(controller = self.ctrlnum)

		return True

	def on_button_release(self, widget, event):
		if event.button == cfg.delete_button:
			self.deleting = False

		if event.button == cfg.select_button:
			self.drawing = False
			self.selecting = False
			self.moving_selection_start = -1
			if self.moving_rows:
				self.moving_rows = False

			if self.selection:
				self.selection = (max(self.selection[0], 0), min(self.selection[1], len(self.trk.ctrl[self.ctrlnum]) - 1))

		if self.moving:
			self.moving = False
			self.on_motion(widget, event)
			self.redraw_env()
			self.tv.redraw(controller = self.ctrlnum)

		if self.drag:
			self.drag = False
			if not self.dragged:
				self.selection = None

			self.redraw_env()
			self.tv.redraw(controller = self.ctrlnum)

		self.undo_buff.add_state()
		return True

	def on_motion(self, widget, event):
		if self.ctrlnum == None:
			return

		if not self.drag and not self.drawing and not self.deleting and not self.moving and not self.selecting and self.moving_selection_start == -1:
			if event.x < self.x_from or event.x > self.x_to:
				return

		# we'd like the keyboard focus, can we take it?
		if not self.tv.keyboard_focus:
			if not self.tv.edit:
				self.tv.keyboard_focus = self
		else:
			if self.tv.keyboard_focus.edit == -1 or self.tv.keyboard_focus.selection:
				self.tv.keyboard_focus = self

		if event.y < 0:
			return

		r = int(min(event.y / (self.tv.txt_height * self.trk.nrows),1) * (self.trk.nrows * self.trk.ctrlpr))
		xw = self.x_to - (self.x_from + self.txt_width)

		going_down = True

		if self.last_r == -1:
			self.last_r = r

		sr = self.last_r
		er = r

		if sr > er:
			er = self.last_r
			sr = r
			going_down = False

		l = er - sr

		if self.last_x == -1:
			self.last_x = event.x

		x = self.last_x
		if l == 0:
			l = 1
			x = event.x

		delta = (event.x - self.last_x) / l

		if not going_down:
			x = event.x
			delta = delta * -1

		for rr in range(l):
			if self.deleting:
				if self.ctrlnum == 0:
					self.trk.set_ctrl(self.ctrlnum, rr + sr, 64 * 128)
				else:
					self.trk.set_ctrl(self.ctrlnum, rr + sr, -1)

			if self.drawing:
				x0 = self.x_from + self.txt_width + (xw / 2)

				v = max(min(round(((x - (self.x_from + self.txt_width)) / xw) * 127), 127), 0)
				if self.ctrlnum == 0:
					self.trk.set_ctrl(self.ctrlnum, rr + sr, round(v * 129))
				else:
					self.trk.set_ctrl(self.ctrlnum, rr + sr, round(v))


				x = x + delta

		self.last_r = r
		if going_down:
			self.last_x = x
		else:
			self.last_x = event.x

		lrow = None

		if self.moving and self.active_row > -1:
			xw = self.x_to - (self.x_from + self.txt_width)
			x0 = self.x_from + self.txt_width + (xw / 2)

			r = min(event.y / self.tv.txt_height, self.trk.nrows)

			v = round(max(min(((event.x - (self.x_from + self.txt_width)) / xw) * 127, 127), 0))
			if self.ignore_x:
				v = self.trk.ctrl[self.ctrlnum][self.active_row].velocity

			lr = self.env[self.active_node]["y"]
			if (r - int(r)) > .5:
				anchor = 1
			else:
				anchor = 0

			if self.snap:
				v = min(round(v / 8) * 8, 127)

			if (r >= self.trk.nrows):
				anchor = 1

			r = int(min(r, self.trk.nrows -1))

			smooth = self.trk.ctrl[self.ctrlnum][self.active_row].smooth
			linked = self.trk.ctrl[self.ctrlnum][self.active_row].linked

			if r != self.active_row and self.trk.ctrl[self.ctrlnum][r].velocity == -1:
				self.trk.ctrl[self.ctrlnum][self.active_row].anchor = 0
				self.trk.ctrl[self.ctrlnum][self.active_row].velocity = -1
				self.trk.ctrl[self.ctrlnum][self.active_row].smooth = 0
				self.trk.ctrl[self.ctrlnum][self.active_row].linked = 0
				self.active_row = r
				self.edit = r
				lrow = self.trk.ctrl[self.ctrlnum][self.active_row]

			if r == self.active_row:
				self.trk.ctrl[self.ctrlnum][self.active_row].velocity = v
				self.trk.ctrl[self.ctrlnum][self.active_row].anchor = anchor
				self.trk.ctrl[self.ctrlnum][self.active_row].smooth = smooth
				self.trk.ctrl[self.ctrlnum][self.active_row].linked = linked
				self.trk.ctrl[self.ctrlnum].refresh()
				self.env = self.trk.get_envelope(self.ctrlnum)

				for n, node in enumerate(self.env):
					ns2 = self.node_size
					r = int(event.y / self.tv.txt_height)
					v = ((event.x - (self.x_from + self.txt_width)) / xw) * 127
					v = max(min(v, 127), 0)
					if abs(node["x"] - v) < ns2 and abs(node["y"] * self.tv.txt_height - r * self.tv.txt_height) < ns2:
						self.active_node = n
						self.edit = r

				self.redraw_env()
				self.tv.redraw(controller = self.ctrlnum)
				return True

		if self.selecting:
			r = min(int(event.y / self.tv.txt_height), self.trk.nrows - 1)
			if r > self.last_selected:
				self.selection = (self.last_selected, r)

			if r <= self.last_selected:
				self.selection = (r, self.last_selected)

			self.tv.redraw(controller = self.ctrlnum)
			return True

		if self.drag:
			r = min(int(event.y / self.tv.txt_height), self.trk.nrows - 1)
			l = self.selection[1] - self.selection[0]
			s = r - self.drag_selection_offset
			self.edit = -1

			if s != 0:
				self.dragged = True

			if l == self.trk.nrows - 1:
				self.selection = 0, self.trk.nrows - 1

				for r in range(len(self.trk.ctrl[self.ctrlnum])):
					rr = r - s

					if rr > self.trk.nrows -1:
						rr -= self.trk.nrows
					if rr < 0:
						rr += self.trk.nrows

					self.trk.ctrl[self.ctrlnum][r].copy(self.drag_content[rr])
			elif r != (self.selection[0] + self.drag_selection_offset):
				self.selection = s, s + l

				for r in range(len(self.trk.ctrl[self.ctrlnum])):
					self.trk.ctrl[self.ctrlnum][r].copy(self.drag_static[r])

					if r >= self.selection[0] and r <= self.selection[1]:
						if self.drag_content[r - self.selection[0]].velocity > -1:
							self.trk.ctrl[self.ctrlnum][r].copy(self.drag_content[r - self.selection[0]])

			self.trk.ctrl[self.ctrlnum].refresh()
			self.env = self.trk.get_envelope(self.ctrlnum)
			self.redraw_env()
			self.tv.redraw(controller = self.ctrlnum)
			return

		l_act_node = self.active_node
		l_act_row = self.active_row

		if self.env:
			ns2 = self.node_size
			self.active_node = -1
			self.active_row = -1

			for n, node in enumerate(self.env):
				r = event.y / self.tv.txt_height
				v = ((event.x - (self.x_from + self.txt_width)) / xw) * 127

				if self.moving:
					v = max(min(v, 127), 0)
					if abs(node["x"] - v) < ns2 and abs(node["y"] * self.tv.txt_height - r * self.tv.txt_height) < ns2:
						if lrow == self.trk.ctrl[self.ctrlnum][int(node["y"])]:
							self.active_node = n
							self.active_row = int(node["y"])
				else:
					if abs(node["x"] - v) < ns2 and abs(node["y"] * self.tv.txt_height - r * self.tv.txt_height) < ns2:
						self.active_node = n
						self.active_row = int(node["y"])

			if self.moving and self.active_node == -1:
				self.active_row = l_act_row
				self.active_node = l_act_node

			if l_act_node != self.active_node:
				self.redraw_env()
				if l_act_node != -1:
					r = int(self.env[l_act_node]["y"])
					self.tv.redraw(r - 1, r + 1)

				if self.active_node != -1:
					r = int(self.env[self.active_node]["y"])
					self.tv.redraw(r - 1, r + 1)

		return True

	def on_scroll(self, event):
		if self.selection:
			return False

		if self.active_node == -1:
			if self.edit != - 1:
				old = self.edit
				self.edit = int(min(max(0, self.edit + event.delta_y), self.trk.nrows - 1))
				self.tv.redraw(old, controller = self.ctrlnum)
				self.tv.redraw(self.edit, controller = self.ctrlnum)
				return True
			return False

		smth = self.trk.ctrl[self.ctrlnum][self.active_row].smooth

		if event.delta_y < 0:
			smth = smth + 1

		if event.delta_y > 0:
			smth = smth - 1

		smth = min(max(smth, 0), 9)

		self.trk.ctrl[self.ctrlnum][self.active_row].smooth = smth
		self.trk.ctrl[self.ctrlnum].refresh()
		self.env = self.trk.get_envelope(self.ctrlnum)
		self.redraw_env()
		self.tv.redraw(controller = self.ctrlnum)
		self.undo_buff.add_state()
		return True

	def to_clipboard(self, doodles = False):
		if not self.selection and not self.edit != -1:
			return

		if not self.selection:
			self.selection = (self.edit, self.edit)

		d = ControllerEditor.clipboard
		if doodles:
			d = ControllerEditor.doodle_clipboard

		d.clear()
		for r in range((self.selection[1] - self.selection[0]) + 1):
			if doodles:
				d.append(self.trk.get_ctrl_rec(self.ctrlnum, r + self.selection[0]))
			else:
				d.append(self.trk.ctrl[self.ctrlnum][r + self.selection[0]].dummy())

	def from_clipboard(self, doodles = False):
		d = ControllerEditor.clipboard
		if doodles:
			d = ControllerEditor.doodle_clipboard

		if not len(d):
			return

		s = max(-1, self.edit)
		e = s + len(d)
		if self.selection:
			s = self.selection[0]
			e = self.selection[1]

		e = min(e, self.trk.nrows)

		if s == -1:
			return

		p = s
		dpr = self.trk.ctrlpr 	# doodles per row
		while(p <= e):
			for r in d:
				if p <= e:
					if doodles:
						for i, val in enumerate(r):
							self.trk.set_ctrl(self.ctrlnum, (dpr * p) + i, val)
					else:
						if self.trk.ctrl[self.ctrlnum][p].velocity == -1:
							self.trk.ctrl[self.ctrlnum][p].copy(r)
				p += 1

		if not self.selection:
			self.edit = min(e, self.trk.nrows - 1)

	def render_doodles(self):
		s = max(-1, self.edit)
		e = s
		if self.selection:
			s = self.selection[0]
			e = self.selection[1]

		e = min(e, self.trk.nrows)

		dpr = self.trk.ctrlpr
		for r in range(s, e + 1):
			cenv = self.trk.get_ctrl_env(self.ctrlnum, r)
			for y, rr in enumerate(cenv):
				if rr != -1:
					self.trk.set_ctrl(self.ctrlnum, (dpr * r) + y, rr)
