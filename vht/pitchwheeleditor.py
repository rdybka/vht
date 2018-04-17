import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gdk, Gtk, Gio
import cairo
import math

from vht import *

class PitchwheelEditor():
	def __init__(self, tv, ctrlnum):
		self.tv = tv
		self.trk = tv.trk
		
		self.x_from = 0
		self.x_to = 0
		self.width = 127
		self.ctrlnum = ctrlnum
		
		self.deleting = False
		self.drawing = False
		self.moving = False
		self.last_r = -1
		self.last_x = -1
		self.ctrl_pressed = False
		self.env = None
		self.env_cr = None
		self.env_sf = None
		self.active_node = -1
		self.node_size = 0
		
	def precalc(self, cr, x_from):
		(x, y, width, height, dx, dy) = cr.text_extents("0")
		self.width = cfg.pitchwheel_editor_char_width * width
		self.x_from = x_from
		self.x_to = x_from + self.width - width

	def configure(self, wdg):
		self.redraw_env()

	def redraw_env(self):
		if self.x_to == 0:
			return

		self.env = self.trk.get_envelope(self.ctrlnum)
	
		# some test data
		if not len(self.env):
			self.trk.env_add_node(self.ctrlnum, 5, 2, 0, 0)
			self.trk.env_add_node(self.ctrlnum, 8, 5, .5, 1)
			self.trk.env_add_node(self.ctrlnum, 120, 10, 0, 1)
			self.trk.env_add_node(self.ctrlnum, 100, 15, 0, 1)
			self.env = self.trk.get_envelope(self.ctrlnum)
	
		recr_cr = False
		
		if self.env_cr:
			if self.env_cr.get_target().get_width() != self.x_to - self.x_from:
				recr_cr = True
			if self.env_cr.get_target().get_height() != self.tv._back_surface.get_height():
				recr_cr = True
		else:
			recr_cr = True
		
		if recr_cr:
			if self.env_sf:
				self.env_sf.finish()
				
			self.env_sf = self.tv._back_surface.create_similar(cairo.CONTENT_COLOR_ALPHA, int(self.x_to - self.x_from), self.tv._back_surface.get_height())
			self.env_cr = cairo.Context(self.env_sf)
			self.env_cr.select_font_face(cfg.seq_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
			self.env_cr.set_font_size(cfg.seq_font_size / 2)
						
		cr = self.env_cr

		node_size = 0

		cr.set_operator(cairo.Operator.CLEAR)
		self.env_cr.paint()
		cr.set_operator(cairo.Operator.OVER)		
		
		if self.env:
			if len(self.env):
				cr.set_source_rgba(*(col * cfg.intensity_lines * 1 for col in cfg.star_colour), 1)
				(x, y, width, height, dx, dy) = cr.text_extents("*")
				node_size = dx
				self.node_size = dx# / 2
				
			# nodes
			for n, node in enumerate(self.env):
				cr.set_source_rgba(*(col * cfg.intensity_lines * 1.5 for col in cfg.star_colour), 1)
				
				xw = self.x_to - self.x_from
				x0 = xw / 2
				
				xx = (node["x"]) - 64
				xx = xx * ((xw / 2) / 64)
				#cr.move_to(x0 + xx, n["y"] * yh)
				
				size_div = 4
				
				if self.active_node == n:
					cr.set_source_rgba(*(col * cfg.intensity_lines * 3 for col in cfg.star_colour), 1)
					txt = "[%.2f:%.2f:%.2f]" % (node["x"], node["y"], node["z"])
					cr.move_to(x0 + xx, node["y"] * self.tv.txt_height)
					cr.show_text(txt)
					size_div = 2
					
				cr.arc((x0 + xx) - ((node_size / size_div) / 2), node["y"] * self.tv.txt_height + (((node_size / size_div) / 2)), node_size / size_div, 0, 2*math.pi)
				
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
				
		yh = self.tv.txt_height
		y0 = r * yh
		
		xw = self.x_to - self.x_from
		x0 = self.x_from + (xw / 2)

		if not self.ctrlnum:
			for c, ct in enumerate(self.trk.ctrls):
				if ct == -1:
					self.ctrlnum = c
					self.env = self.trk.get_envelope(self.ctrlnum)
		
		cr.set_line_width(1.0)
		cr.set_source_rgba(*(col * cfg.intensity_txt for col in cfg.colour), .2)
		cr.rectangle(self.x_from, r * self.tv.txt_height, xw, yh)
		cr.fill()
				
		if self.ctrlnum == None:
			cr.set_source_rgba(*(col * cfg.intensity_txt for col in cfg.colour), .3)
			cr.move_to(x0, r * yh)
			cr.line_to(x0, (r + 1) * yh)
			cr.stroke()
			return
		
		ctrl = self.trk.get_ctrl(self.ctrlnum, r)
		if not len(ctrl):
			return
			
		yp = yh / len(ctrl)

		cr.set_source_rgba(*(col * cfg.intensity_txt for col in cfg.colour), .7)
		for v in ctrl:
			xx = (v / 127) - 64
			xx = xx * ((xw / 2) / 64)
			
			if v == -1:
				xx = 0
				
			if x0 + xx > self.x_to:
				xx = self.x_to - x0

			cr.rectangle(x0, y0, xx, yp)
			cr.fill()
			
			y0 = y0 + yp

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
			cr.set_source_surface(self.env_sf, self.x_from, 0)
			cr.rectangle(self.x_from, r * yh, xw, yh)
			cr.fill()
		
	def on_key_press(self, widget, event):
		if event.state & Gdk.ModifierType.CONTROL_MASK:
			self.ctrl_pressed = True
		return True
		
	def on_key_release(self, widget, event):
		if event.state & Gdk.ModifierType.CONTROL_MASK:
			self.ctrl_pressed = False
		return True
		
	def on_button_press(self, widget, event):
		if event.x < self.x_from or event.x > self.x_to:
			return
		
		ctrl = False
		
		if event.state & Gdk.ModifierType.CONTROL_MASK:
			ctrl = True
		
		if self.active_node != -1:
			node = self.env[self.active_node]

			if event.button == cfg.delete_button:
				#r = int(node["y"])
				self.trk.env_del_node(self.ctrlnum, self.active_node)
				self.active_node = -1
				self.env = self.trk.get_envelope(self.ctrlnum)
				self.redraw_env()
				self.tv.redraw(controller = self.ctrlnum)
				return True
			
			if event.button == cfg.select_button:
				if event.type == Gdk.EventType._2BUTTON_PRESS or event.type == Gdk.EventType._3BUTTON_PRESS:
					l = node["l"]

					if l == 0:
						l = 1
					else:
						l = 0
									
					self.trk.env_set_node(self.ctrlnum, self.active_node, node["x"], node["y"], node["z"], l)
					self.env = self.trk.get_envelope(self.ctrlnum)
					self.redraw_env()
					self.tv.redraw(controller = self.ctrlnum)
				else:
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
			
		if ctrl:
			xw = self.x_to - self.x_from
			x0 = self.x_from + (xw / 2)
			v = max(min(((event.x - self.x_from) / xw) * 127, 127), 0)
			
			self.trk.env_add_node(self.ctrlnum, v, event.y / self.tv.txt_height, 0, 1)
			self.env = self.trk.get_envelope(self.ctrlnum)
			
			self.on_motion(widget, event)
			
			self.redraw_env()
			
			self.tv.redraw(controller = self.ctrlnum)
			
		return True
		
	def on_button_release(self, widget, event):
		if event.button == cfg.delete_button:
			self.deleting = False

		if event.button == cfg.select_button:
			self.drawing = False

		if self.moving:
			self.moving = False
			
		return True
		
	def on_motion(self, widget, event):
		if self.ctrlnum == None:
			return;
		
		if not self.drawing and not self.deleting:
			if event.x < self.x_from or event.x > self.x_to:
				return
		
		if event.y < 0:
			return
		
		r = int(min(event.y / (self.tv.txt_height * self.trk.nrows),1) * (self.trk.nrows * self.trk.ctrlpr))
		xw = self.x_to - self.x_from
		
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
				self.trk.set_ctrl(self.ctrlnum, rr + sr, 64 * 128)
		
			if self.drawing:
				x0 = self.x_from + (xw / 2)

				v = max(min(round(((x - self.x_from) / xw) * 127), 127), 0)
				self.trk.set_ctrl(self.ctrlnum, rr + sr, round(v * 129))
				x = x + delta
							
		self.last_r = r
		if going_down:
			self.last_x = x
		else:
			self.last_x = event.x
		
		# moving node
		if self.moving:
			xw = self.x_to - self.x_from
			x0 = self.x_from + (xw / 2)
			v = max(min(((event.x - self.x_from) / xw) * 127, 127), 0)
			r = event.y / self.tv.txt_height
						
			lr = self.env[self.active_node]["y"]
			
			self.trk.env_set_node(self.ctrlnum, self.active_node, v, r, self.env[self.active_node]["z"])
			self.env = self.trk.get_envelope(self.ctrlnum)
			self.redraw_env()
			
			#self.tv.redraw(lr - 2, lr + 2)
			self.tv.redraw(controller = self.ctrlnum)
					
		l_act_node = self.active_node
				
		if self.env:
			ns2 = self.node_size
			self.active_node = -1
			
			for n, node in enumerate(self.env):
				v = max(min(((event.x - self.x_from) / xw) * 127, 127), 0)
				r = event.y / self.tv.txt_height
				
				if abs(node["x"] - v) < ns2 and abs(node["y"] * self.tv.txt_height - r * self.tv.txt_height) < ns2:
					self.active_node = n
				
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
		if self.active_node == -1:
			return False
		
		z = self.env[self.active_node]["z"]
		
		if event.delta_y > 0:
			z = z + .05
		
		if event.delta_y < 0:
			z = z - .05
		
		if z < 0:
			z = 0
			
		if z > 1:
			z = 1;
			
		self.trk.env_set_node(self.ctrlnum, self.active_node, self.env[self.active_node]["x"], self.env[self.active_node]["y"], z)
		self.env = self.trk.get_envelope(self.ctrlnum)
		self.redraw_env()
		self.tv.redraw()
		return True
