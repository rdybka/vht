import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio
from trackpropview import TrackPropView
from pypms import pms
import cairo

class PropView(Gtk.ScrolledWindow):
	def __init__(self, seqview):
		Gtk.ScrolledWindow.__init__(self)
		self.connect("draw", self.on_draw);
		self.connect("leave-notify-event", self.on_leave)				
		
		self.seqview = seqview
		self.seq = seqview.seq;
		
		self._track_box = Gtk.Box()
		self._track_box.set_spacing(0)
		pms.clear_popups = self.clear_popups
		
		self._track_box.add(TrackPropView(None, self.seq, self.seqview, self))

		self.build()
		
		self.set_policy(Gtk.PolicyType.EXTERNAL, Gtk.PolicyType.NEVER)
		self.add_with_viewport(self._track_box)
		self._track_box.show_all()
			
	def del_track(self, trk):
		i = 0
		for wdg in self._track_box.get_children()[1:]:
			if wdg.trk.index == trk.index:
				self.seq.del_track(i)
				return
				
			i += 1

	def on_leave(self, wdg, prm):
		if prm.detail == Gdk.NotifyType.NONLINEAR:
			self.clear_popups()

	def add_track(self, trk):
		t = TrackPropView(trk, self.seq, self.seqview, self)
		self._track_box.pack_start(t, False, True, 0)
		t.show()

	def reindex_tracks(self):
		i = 0
		for wdg in self._track_box.get_children()[1:]:
			wdg.trk.index = i
			i += 1
		
		i = 0
		for wdg in self.seqview._track_box.get_children()[1:]:
			wdg.trk.index = i
			i += 1
			
	def move_track(self, trk, offs):
		wdg = self._track_box.get_children()[1:][trk.index]
		self._track_box.reorder_child(wdg, (trk.index + 1) + offs)
		wdg = self.seqview._track_box.get_children()[1:][trk.index]
		self.seqview._track_box.reorder_child(wdg, (trk.index + 1) + offs)
		
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
		self.move_track(trk, trk.index * -1)

	def move_last(self, trk):
		self.move_track(trk, (len(self.seq) - trk.index) - 1)

	def build(self):
		for trk in self.seq:
			self.add_track(trk)
			
	def clear_popups(self):
		for wdg in self._track_box.get_children():
			wdg.popover.popdown()

	def on_draw(self, widget, cr):
		w = widget.get_allocated_width()
		h = widget.get_allocated_height()
		cr.set_source_rgb(*(col * pms.cfg.intensity_background for col in pms.cfg.colour))
		cr.rectangle(0, 0, w, h)
		cr.fill()
		
		super()
