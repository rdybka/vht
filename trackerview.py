import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio
import cairo
import trackview

class TrackerView(Gtk.ScrolledWindow):
	def __init__(self, pms_handle):
		Gtk.ScrolledWindow.__init__(self)
		
		self.mod = pms_handle

		self.trackBox = Gtk.Box()
		self.trackBox.add(trackview.TrackView())
		self.trackBox.add(trackview.TrackView(1))
		
		self.trackBox.set_spacing(1)
		
		self.add_with_viewport(self.trackBox)

