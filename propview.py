import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio
import cairo

from trackpropview import TrackPropView

from pypms import pms

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

	def on_leave(self, wdg, prm):
		if prm.detail == Gdk.NotifyType.NONLINEAR:
			self.clear_popups()

	def add_track(self, trk):
		t = TrackPropView(trk, self.seq, self.seqview, self)
		self._track_box.pack_start(t, False, True, 0)
		t.show()

	def del_track(self, trk):
		ind = None
		for wdg in self._track_box.get_children():
			if wdg.trk == trk:
				ind = trk.index
				wdg.destroy()
				
		if ind:
			self.seq.del_track(ind)

	def reorder(self):
		print("reorder props")
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
