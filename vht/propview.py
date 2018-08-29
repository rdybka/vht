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
		for wdg in self.seqview.get_tracks():
			wdg.trk.index = i
			i += 1
			
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
		self.move_track(trk, trk.index * -1)

	def move_last(self, trk):
		self.move_track(trk, (len(self.seq) - 1)- trk.index)

	def clear_popups(self):
		for wdg in self._track_box.get_children() + [self.seqview._side_prop]:
			wdg.popover.popdown()
			wdg.popped = False
			wdg.redraw()
		
		#self.seqview._side_prop.popover.popdown()

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
