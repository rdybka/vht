import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio
import cairo

from vht import *

class BlackButton(Gtk.Button):
	def __init__(self, txt):
		Gtk.Label.__init__(self, txt)
		self.txt = txt
		self.connect("draw", self.on_draw)
		self.set_margin_top(3)
		self.set_margin_left(3)
		self.set_margin_bottom(3)
		self.set_margin_right(3)
		
	def on_draw(self, widget, cr):
		state = widget.get_state_flags()
		
		hover = False
		if state & Gtk.StateFlags.PRELIGHT:
			hover = True
		
		active = False
		if state & Gtk.StateFlags.ACTIVE:
			active = True

		w = widget.get_allocated_width()
		h = widget.get_allocated_height()
		
		cr.set_source_rgb(*(col * cfg.intensity_background for col in cfg.colour))
		if active:
			cr.set_source_rgb(*(col * cfg.intensity_txt_highlight for col in cfg.colour))
		
		cr.move_to(0,0)
		cr.line_to(w, 0)
		cr.line_to(w, 0)
		cr.line_to(w, h * .8)
		cr.line_to(w - h * .2, h)
		cr.line_to(0, h)
		cr.line_to(0, 0)
		cr.fill()

		cr.set_source_rgb(*(col * cfg.intensity_txt for col in cfg.colour))
		if hover:
			cr.set_source_rgb(*(col * cfg.intensity_txt_highlight for col in cfg.colour))

		if active:
			cr.set_source_rgb(*(col * cfg.intensity_background for col in cfg.colour))	

		cr.move_to(0,0)
		cr.line_to(w, 0)
		cr.line_to(w, 0)
		cr.line_to(w, h * .8)
		cr.line_to(w - h * .2, h)
		cr.line_to(0, h)
		cr.line_to(0, 0)
		cr.stroke()

		(x, y, width, height, dx, dy) = cr.text_extents(self.txt)
		cr.move_to((w - width) / 2, h / 2 + (height / 2))
		cr.show_text(self.txt)

		return True
