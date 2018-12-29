import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio, GObject
import cairo

from vht import *
from vht.controlrow import ControlRow

class ControllersView(Gtk.ScrolledWindow):
	def __init__(self, trk, trkview):
		super(ControllersView, self).__init__()
		
		self.trk = trk
		self.trkview = trkview

		self.box = Gtk.Box()
		self.box.set_orientation(Gtk.Orientation.VERTICAL)
		self.box.set_homogeneous(False)
		self.box.set_spacing(2)
		
		if len(self.trk.ctrls) == 1:
			rw = ControlRow(trk, -1)
			self.box.pack_start(rw, False, False, 0)

		self.add(self.box)
		self.show_all()

