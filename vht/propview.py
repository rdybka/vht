# propview.py - Valhalla Tracker
#
# Copyright (C) 2019 Remigiusz Dybka - remigiusz.dybka@gmail.com
# @schtixfnord
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

from vht import *
from vht.trackpropview import TrackPropView
from vht.trackview import TrackView

class PropView(Gtk.ScrolledWindow):
	def __init__(self, seqview):
		Gtk.ScrolledWindow.__init__(self)
		self.connect("draw", self.on_draw);
		self.connect("leave-notify-event", self.on_leave)

		self.seqview = seqview
		self.seq = seqview.seq;

		self.last_font_size = cfg.seq_font_size

		self._track_box = Gtk.Box()
		self._track_box.set_spacing(0)
		mod.clear_popups = self.clear_popups

		self.set_policy(Gtk.PolicyType.EXTERNAL, Gtk.PolicyType.NEVER)
		self.add_with_viewport(self._track_box)
		self._track_box.show_all()

	def del_track(self, trk):
		track_pv = self._track_box.get_children()[trk.index]
		track_pv.popover.popdown()
		track_pv.destroy()

	def on_leave(self, wdg, prm):
		pass

	def add_track(self, trk, trkview):
		t = TrackPropView(trk, trkview, self.seq, self.seqview, self)
		self._track_box.pack_start(t, False, True, 0)
		t.show()

	def reindex_tracks(self):
		i = 0
		for i, wdg in enumerate(self.seqview.get_tracks()):
			wdg.trk.index = i

	def move_track(self, trk, offs):
		wdg = self._track_box.get_children()[trk.index]
		self._track_box.reorder_child(wdg, (trk.index) + offs)
		wdg = self.seqview._track_box.get_children()[trk.index]
		self.seqview._track_box.reorder_child(wdg, (trk.index) + offs)
		self.seq.swap_track(trk.index, trk.index + offs)
		self.reindex_tracks()

	def move_left(self, trk):
		if trk.index is 0:
			return

		self.move_track(trk, -1)

	def move_right(self, trk):
		if trk.index is len(self.seq):
			return

		self.move_track(trk, 1)

	def move_first(self, trk):
		for i in range(trk.index):
			self.move_track(trk, -1)

	def move_last(self, trk):
		for i in range((len(self.seq) - 1)- trk.index):
			self.move_track(trk, 1)

	def clear_popups(self, ignore = None):
		for wdg in self._track_box.get_children() + [self.seqview._side_prop]:
			if wdg.get_realized():
				if ignore != wdg.popover:
					wdg.popover.unpop()
					wdg.popped = False
					wdg.redraw()

	def redraw(self, index = -1):
		for wdg in self._track_box.get_children():
			if wdg.trk.index == index or index == -1:
				wdg.redraw()

		self.queue_draw()

	def on_draw(self, widget, cr):
		w = widget.get_allocated_width()
		h = widget.get_allocated_height()
		cr.set_source_rgb(*(col * cfg.intensity_background for col in cfg.colour))
		cr.rectangle(0, 0, w, h)
		cr.fill()

		for wdg in self._track_box.get_children():
			if self.last_font_size != cfg.seq_font_size:
				wdg.redraw()

		self.last_font_size = cfg.seq_font_size
		super()
