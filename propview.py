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
		
		self.add_tick_callback(self.tick)
		
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
			
	def tick(self, wdg, param):
		for wdg in self._track_box.get_children()[1:]:
				wdg.queue_draw()
			
		return 1

	def del_track(self, trk):
		i = 0
		for wdg in self._track_box.get_children()[1:]:
			if wdg.trk.index == trk.index:
				self.seq.del_track(i)
				return
				
			i = i + 1

	def on_leave(self, wdg, prm):
		if prm.detail == Gdk.NotifyType.NONLINEAR:
			self.clear_popups()

	def add_track(self, trk):
		t = TrackPropView(trk, self.seq, self.seqview, self)
		self._track_box.pack_start(t, False, True, 0)
		t.show()

	#self._track_box.reorder_child(wdg, wdg.trk.index  1)

	def build(self):
		for trk in self.seq:
			self.add_track(trk)
			
	def clear_popups(self):
		for wdg in self._track_box.get_children():
			wdg.popover.popdown()

	def on_draw(self, widget, cr):
		w = widget.get_allocated_width()
		h = widget.get_allocated_height()
		cr.set_source_rgb(0,.3,0)
		cr.rectangle(0, 0, w, h)
		cr.fill()
		
		super()
