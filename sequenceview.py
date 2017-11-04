import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio
import cairo
from trackview import TrackView

from pypms import pms

class SequenceView(Gtk.ScrolledWindow):
	def __init__(self, seq):
		Gtk.ScrolledWindow.__init__(self)
		self.set_events(Gdk.EventMask.POINTER_MOTION_MASK |
			Gdk.EventMask.SCROLL_MASK |
			Gdk.EventMask.ENTER_NOTIFY_MASK |
			Gdk.EventMask.KEY_PRESS_MASK |
			Gdk.EventMask.KEY_RELEASE_MASK)
			
		self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
				
		self.connect("draw", self.on_draw)
		self.connect("motion-notify-event", self.on_motion)
		self.connect("scroll-event", self.on_scroll)
		self.connect("key-press-event", self.on_key_press)
		self.connect("key-release-event", self.on_key_release)
		self.connect("enter-notify-event", self.on_enter)
		
		self.set_can_focus(True)
		self.add_tick_callback(self.tick)
	
		self.seq = seq;
		self.last_count = len(seq)
		self.control_down = False
		self.prop_view = None

		self.def_new_track_width = 0
				
		self._track_box = Gtk.Box()
		self._track_box.set_spacing(0)
		self.add_track(None)
		self.build()

		self._track_box.show_all()

		self.add_with_viewport(self._track_box)

	def on_key_press(self, widget, event):
		if event.keyval == 65507 or event.keyval == 65508:
			self.control_down = True
		return False

	def on_key_release(self, widget, event):
		if event.keyval == 65507 or event.keyval == 65508:
			self.control_down = False
		return False

	def on_scroll(self, widget, event):
		if self.control_down: # we're zooming!
			if event.delta_y > 0:
				pms.cfg.seq_font_size -= 1
			
			if event.delta_y < 0:
				pms.cfg.seq_font_size += 1
			
			if pms.cfg.seq_font_size < 1:
				pms.cfg.seq_font_size = 1

			pms.cfg.pointer_height = .7 * pms.cfg.seq_font_size

			self.redraw_track(None)
			self.prop_view.queue_draw()
		return False

	def on_motion(self, widget, event):
		#self.grab_focus()
		pms.clear_popups()
	
	def add_track(self, trk):
		t = TrackView(self.seq, trk)
		
		self._track_box.pack_start(t, False, True, 0)
		#t.set_size_request(self.def_new_track_width, 10)
		t.show()

	def del_track(self, trk):
		for wdg in self.get_tracks()[1:]:
			if wdg.trk.index == trk.index:
				TrackView.track_views.remove(wdg)
				wdg.destroy()
				return
	
	def redraw_track(self, trk = None):
		for wdg in self.get_tracks():
			rdr = False
			if not trk:
				rdr = True
			else:
				if wdg.trk:
					if wdg.trk.index == trk.index:
						rdr = True	 
			if rdr:
				wdg.redraw()
				
		self.queue_draw()
			
	def build(self):
		for trk in self.seq:
			self.add_track(trk)
	
	def recalculate_row_spacing(self):
		minspc = 1.0
		
		for wdg in self.get_tracks():
			if wdg.trk == None:
				spc = 1.0
			else:
				spc = wdg.trk.nsrows / wdg.trk.nrows
			wdg.spacing = spc

			if spc < minspc:
				minspc = spc
				
		if minspc < 1.0:
			for wdg in self.get_tracks():
				wdg.spacing /= minspc

		self.redraw_track(None)
		self.queue_draw()
	
	def tick(self, wdg, param):
		for wdg in self.get_tracks():
				wdg.tick()
		return 1
	
	def on_draw(self, widget, cr):
		w = widget.get_allocated_width()
		h = widget.get_allocated_height()
		
		cr.set_source_rgb(*(col * pms.cfg.intensity_background for col in pms.cfg.colour))
		cr.rectangle(0, 0, w, h)
		cr.fill()
		super()

	def get_tracks(self):
		ret = []
		for wdg in self._track_box.get_children():
			ret.append(wdg)

		return ret
	
	def on_enter(self, wdg, prm):
		self.grab_focus()
