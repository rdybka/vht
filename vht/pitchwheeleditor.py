import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gdk, Gtk, Gio
import cairo
import math

from vht import *

class PitchwheelEditor():
	def __init__(self, tv):
		self.tv = tv
		self.trk = tv.trk
		
		self.x_from = 0
		self.x_to = 0
		self.width = 127
		self.ctrlnum = None
		self.deleting = False
		self.drawing = False
		self.last_r = -1
		self.last_x = -1
			
	def precalc(self, cr, x_from):
		(x, y, width, height, dx, dy) = cr.text_extents("0")
		self.width = max((cfg.pitchwheel_editor_char_width * width), 99)
		self.x_from = x_from
		self.x_to = x_from + self.width - width
			
	def draw(self, cr, r):
		yh = self.tv.txt_height
		y0 = r * yh
		
		xw = self.x_to - self.x_from
		x0 = self.x_from + (xw / 2)

		if not self.ctrlnum:
			for c, ct in enumerate(self.trk.ctrls):
				if ct == -1:
					self.ctrlnum = c
		
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
				
	def on_key_press(self, widget, event):
		#if cfg.key["hold_editor"].matches(event):	
		return True
		
	def on_key_release(self, widget, event):
		return True
		
	def on_button_press(self, widget, event):
		if event.x < self.x_from or event.x > self.x_to:
			return
		
		if event.button == cfg.delete_button:
			self.deleting = True
			self.last_r = -1
			self.last_x = -1
			
		if event.button == cfg.select_button:
			self.drawing = True
			self.last_r = -1
			self.last_x = -1
			
		return True
		
	def on_button_release(self, widget, event):
		if event.button == cfg.delete_button:
			self.deleting = False

		if event.button == cfg.select_button:
			self.drawing = False

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
				xw = self.x_to - self.x_from
				x0 = self.x_from + (xw / 2)

				v = max(min(round(((x - self.x_from) / xw) * 127), 127), 0)
				self.trk.set_ctrl(self.ctrlnum, rr + sr, round(v * 129))
				x = x + delta
							
		self.last_r = r
		if going_down:
			self.last_x = x
		else:
			self.last_x = event.x
		
		return True
