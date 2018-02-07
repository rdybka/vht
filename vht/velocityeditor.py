import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gdk, Gtk, Gio
import cairo

from vht import *

class VelocityEditor():
	def __init__(self, tv, col, row, event):
		self.col = col
		self.row = row
		self.tv = tv
		self.event_y = event.y
		
		self.trk = tv.trk
		
		self.confirmed = False
		self.clearing = False
		self.lock = False
		self.locked = self.trk[col][row].velocity
		self.start_value = self.locked
		
		self.x_from = 0
		self.x_to = 0
		self.width = 127
	
	def precalc(self, cr):
		(x, y, width, height, dx, dy) = cr.text_extents("0")
		self.width = max((cfg.velocity_editor_char_width * width), 127)
		
		if self.tv.show_timeshift:
			(x, y, wdth, height, dx, dy) = cr.text_extents("000 0000")
			
			self.x_from = (self.col * self.tv.txt_width + dx) - (width / 1.2)
			self.x_to = self.width
		else:
			self.x_from = (self.col * self.tv.txt_width + self.tv.txt_width) - (width / 1.2)
			self.x_to = self.width
			
	def draw(self, cr, col, r, rw):
		yh = cfg.editor_row_height * self.tv.txt_height
		yp = ((self.tv.txt_height - yh) / 2.0)
					
		cr.set_line_width(1.0)
		cr.set_source_rgba(*(col * cfg.intensity_txt for col in cfg.colour), .5)
		cr.rectangle(self.x_from, r * self.tv.txt_height + yp, (self.x_to / 127.0) * rw.velocity, yh)
		cr.fill()
					
		cr.set_source_rgba(*(col * cfg.intensity_txt for col in cfg.colour), 1.0)
		cr.rectangle(self.x_from, r * self.tv.txt_height + yp, self.x_to, yh)
		cr.stroke()

	def on_key_press(self, widget, event):
		if cfg.key["hold_editor"].matches(event):	
			if not self.clearing:
				if not self.lock:
					self.lock = True
					if not self.confirmed:
						self.locked = self.tv.trk[self.col][self.row].velocity
		
	def on_key_release(self, widget, event):
		if self.clearing:
			return False
			
		if not self.confirmed:
			self.lock = False
			self.locked = self.tv.trk[self.col][self.row].velocity

		if self.confirmed:
			self.lock = False
		
	def on_motion(self, widget, event):
		# edit single velocity in place
		if not self.clearing and not self.confirmed and not self.lock:
			if event.x < self.x_from:
				vel = self.trk[self.col][self.row].velocity
				
				vel = self.start_value - ((event.y - self.event_y) / cfg.drag_edit_divisor)
				vel = max(min(vel, 127), 0)
						
				self.locked = vel
						
				self.tv.trk[self.col][self.row].velocity = vel
				self.tv.redraw(self.row)
				return True
		
		if not self.confirmed:
			if event.x >= self.x_from and event.x <= self.x_from + self.x_to:
				self.confirmed = True
		
			if not self.confirmed:
				return False
			
		new_hover_row = min(int(event.y / self.tv.txt_height), self.tv.trk.nrows - 1)
		new_hover_column = min(int(event.x / self.tv.txt_width), len(self.tv.trk) -1)

		if self.tv.trk[self.col][self.row].type != 1:
			return False

			
		y1 = new_hover_row * self.tv.txt_height
		y2 = y1 + self.tv.txt_height
		
		vel = cfg.default_velocity
			
		yy = (self.tv.txt_height - cfg.editor_row_height * self.tv.txt_height) / 2.0
		if event.y > y1 and event.y < y2:
			vel = min(max(((event.x - self.x_from) / self.x_to) * 127.0, 0), 127)
				
		if self.lock:
			vel = self.locked

		if self.clearing:
			vel = cfg.default_velocity
		
		if new_hover_row > -1:
			if not self.lock and self.tv.trk[self.col][new_hover_row].type == 1:
				self.locked = vel
				
			self.tv.trk[self.col][new_hover_row].velocity = vel
			self.tv.redraw(new_hover_row, new_hover_row)
		return True