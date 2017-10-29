import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio
import cairo
from trackview import TrackView
from tracksideview import TrackSideView

from pypms import pms

class SequenceView(Gtk.ScrolledWindow):
	def __init__(self, seq):
		Gtk.Overlay.__init__(self)
		self.set_events(Gdk.EventMask.POINTER_MOTION_MASK | 
			Gdk.EventMask.BUTTON_PRESS_MASK |
			Gdk.EventMask.BUTTON_RELEASE_MASK)

		self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
				
		self.connect("draw", self.on_draw);
		self.connect("motion-notify-event", self.on_motion);
		
		self.add_tick_callback(self.tick)
	
		self.seq = seq;
		self.last_count = len(seq)

		self.def_new_track_width = 0
		
		self._track_box = Gtk.Box()
		self._track_box.set_spacing(0)
		self._track_box.pack_start(TrackSideView(self.seq), False, True, 0)		
		self.build()

		self._track_box.show_all()

		self.add_with_viewport(self._track_box)

	def on_motion(self, widget, event):
		pms.clear_popups()
	
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
	
	def redraw_track(self, trk = None):
		for wdg in self._track_box.get_children()[1:]:
			if not trk or wdg.trk.index == trk.index:
				wdg.queue_resize()
				wdg.redraw()
				wdg.queue_draw()
				return
				
	def build(self):
		for trk in self.seq:
			self.add_track(trk)
	
	def recalculate_row_spacing(self):
		minspc = 1.0
		
		for wdg in self._track_box.get_children():
			if isinstance(wdg, TrackSideView):
				spc = 1.0
			else:
				spc = wdg.trk.nsrows / wdg.trk.nrows
			wdg.spacing = spc
			if spc < minspc:
				minspc = spc
				
		if minspc < 1.0:
			for wdg in self._track_box.get_children():
				wdg.spacing /= minspc
		
		for wdg in self._track_box.get_children():
			wdg.redraw()
		
		self.queue_draw()
	
	def tick(self, wdg, param):
		#self.recalculate_row_spacing()
		for wdg in self._track_box.get_children():
			wdg.tick()
			wdg.queue_draw()
		return 1
	
	def on_draw(self, widget, cr):
		w = widget.get_allocated_width()
		h = widget.get_allocated_height()
		
		cr.set_source_rgb(*(col * pms.cfg.intensity_background for col in pms.cfg.colour))
		cr.rectangle(0, 0, w, h)
		cr.fill()

		super()
