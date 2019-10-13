# sequencelistview.py - Valhalla Tracker
#
# Copyright (C) 2019 Remigiusz Dybka - remigiusz.dybka@gmail.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio
import cairo
import random
from datetime import datetime
from vht import *

class SequenceListView(Gtk.DrawingArea):
	def __init__(self):
		super(TrackPropView, self).__init__()

		self.set_events(Gdk.EventMask.POINTER_MOTION_MASK |
			Gdk.EventMask.SCROLL_MASK |
			Gdk.EventMask.BUTTON_PRESS_MASK |
			Gdk.EventMask.BUTTON_RELEASE_MASK |
			Gdk.EventMask.KEY_PRESS_MASK |
			Gdk.EventMask.KEY_RELEASE_MASK)

		self.connect("button-press-event", self.on_click)
		self.connect("motion-notify-event", self.on_mouse_move)
		self.connect("draw", self.on_draw)
		self.connect("configure-event", self.on_configure)

		self.add_tick_callback(self.tick)

		self._surface = None
		self._context = None

	def configure(self):
		win = self.get_window()
		if not win:
			return

		if self._surface:
			self._surface.finish()

		self._surface = self.get_window().create_similar_surface(cairo.CONTENT_COLOR,
			self.get_allocated_width(),
			self.get_allocated_height())

		self._context = cairo.Context(self._surface)
		self._context.set_antialias(cairo.ANTIALIAS_NONE)
		self._context.set_line_width((cfg.seq_font_size / 6.0) * cfg.seq_line_width)
		self._context.select_font_face(cfg.seq_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)

	def on_configure(self, wdg, event):
		self.redraw()
		return True

	def on_mouse_move(self, widget, data):
		pass

	def on_click(self, widget, data):
		pass

	def redraw(self, col):
		cr = self._context

		w = self.get_allocated_width()
		h = self.get_allocated_height()

		if self.trk:
			w = self.trkview.width

		self._context.set_font_size(cfg.seq_font_size)
		cr.set_source_rgb(*(col * cfg.intensity_background for col in cfg.colour))
		cr.rectangle(0, 0, w, h)
		cr.fill()

		self.queue_draw()

	def on_draw(self, widget, cr):
		cr.set_source_surface(self._surface, 0, 0)
		cr.paint()
		return False

	def tick(self, wdg, param):
		return True
