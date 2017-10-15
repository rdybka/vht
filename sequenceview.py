import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio
import cairo
from trackview import TrackView
from tracksideview import TrackSideView

class SequenceView(Gtk.ScrolledWindow):
	def __init__(self, pms_handle):
		Gtk.ScrolledWindow.__init__(self)
		
		self._pms_handle = pms_handle
		self.seq = self._pms_handle[0];
		self._track_box = Gtk.Box()

		self._track_box.add(TrackSideView(self.seq))
		for trk in self.seq:
			self._track_box.add(TrackView(trk))
		
		self._track_box.set_spacing(0)
		
		self.add_with_viewport(self._track_box)

