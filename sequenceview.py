import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio
import cairo
from trackview import TrackView
from tracksideview import TrackSideView

from pypms import pms

class SequenceView(Gtk.ScrolledWindow):
	def __init__(self, seq):
		Gtk.ScrolledWindow.__init__(self)
		self.set_events(Gdk.EventMask.POINTER_MOTION_MASK | 
			Gdk.EventMask.BUTTON_PRESS_MASK |
			Gdk.EventMask.BUTTON_RELEASE_MASK)
		
		self.connect("draw", self.on_draw);
		self.connect("motion-notify-event", self.on_motion);
		self.connect("button-press-event", self.on_button);
		
		self.add_tick_callback(self.tick)
	
		self.seq = seq;
		self.last_count = len(seq)

		self.def_new_track_width = 0
		
		self._track_box = Gtk.Box()
		self._track_box.set_spacing(0)
		self._track_box.pack_start(TrackSideView(self.seq), False, True, 0)		
		self.build()
		
		self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
		self.add_with_viewport(self._track_box)
		self._track_box.show_all()
	
	def on_motion(self, widget, event):
		pms.clear_popups()
	
	def on_button(self, widget, event):
		pass
	
	def add_track(self, trk):
		t = TrackView(trk)
		self._track_box.pack_start(t, False, True, 0)
		t.set_size_request(self.def_new_track_width, 10)
		t.show()

	def del_track(self, trk):
		for wdg in self._track_box.get_children()[1:]:
			if wdg.trk.index == trk.index:
				wdg.destroy()
				return
	
	#self._track_box.reorder_child(wdg, wdg.trk.index  1)
		
	def build(self):
		for trk in self.seq:
			self.add_track(trk)
	
	def tick(self, wdg, param):
		for wdg in self._track_box.get_children()[1:]:
				wdg.queue_draw()
		
		return 1
	
	def on_draw(self, widget, cr):
		w = widget.get_allocated_width()
		h = widget.get_allocated_height()
		
		if not self.def_new_track_width:
			cr.select_font_face("Roboto Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL )
			cr.set_font_size(12)
			(x, y, width, height, dx, dy) = cr.text_extents("000 000")
			self.def_new_track_width = width + 12
		
		cr.set_source_rgb(0,.3,0)
		cr.rectangle(0, 0, w, h)
		cr.fill()

		super()
