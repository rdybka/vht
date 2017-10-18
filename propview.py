import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio
import cairo

from trackpropview import TrackPropView

class PropView(Gtk.Bin):
	def __init__(self, seqview):
		Gtk.Bin.__init__(self)
		self.connect("draw", self.on_draw);
		self.tick_ref = self.add_tick_callback(self.tick)
		
		self.seqview = seqview
		self.seq = seqview.seq;
		
		self._track_box = Gtk.Box()
		self._track_box.add(TrackPropView(self.clear_popups, None, self.seq, self.seqview, self))

		self.build()
		
		self._track_box.set_spacing(0)
		self.add(self._track_box)
		self._track_box.show_all()

	def add_track(self, trk):
		t = TrackPropView(self.clear_popups, trk, self.seq, self.seqview, self)
		self._track_box.add(t)
		t.show()
	
	def del_track(self, trk):
		for wdg in self._track_box.get_children()[1:]:
			if wdg.trk == trk:
				self._track_box.remove(wdg)

	def reorder(self):
		print("reorder props")
		#self._track_box.reorder_child(wdg, wdg.trk.index  1)
	
	def build(self):
		for trk in self.seq:
			self.add_track(trk)

	def tick(self, wdg, param):
		self.queue_draw()
		return 1
			
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
