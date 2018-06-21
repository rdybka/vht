import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from vht import cfg

class BlackLabel(Gtk.Label):
	def __init__(self, txt):
		Gtk.Label.__init__(self, txt)
		self.txt = txt
		self.connect("draw", self.on_draw)
		self.set_margin_top(3)
		self.set_margin_left(3)
		self.set_margin_bottom(3)
		self.set_margin_right(3)

	def on_draw(self, widget, cr):
		w = widget.get_allocated_width()
		h = widget.get_allocated_height()

		cr.set_source_rgb(*(col * cfg.intensity_background for col in cfg.colour))
		cr.rectangle(0, 0, w, h)
		cr.fill()

		cr.set_source_rgb(*(col * cfg.intensity_txt for col in cfg.colour))
		(x, y, width, height, dx, dy) = cr.text_extents(self.txt)
		cr.move_to((w - width) / 2, h / 2 + (height / 2))
		cr.show_text(self.txt)

		return True
