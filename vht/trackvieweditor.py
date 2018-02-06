import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gdk, Gtk, Gio
import cairo

from vht import *

class TrackViewEditor():
	def __init__(self, tv):
		self.tv = tv
		
	def get_required_width(self):
		return 127
	
	def on_button_press(self, event):
		return False
		
	def on_button_release(self, event):
		return False
		
	def on_motion(self, event):
		return False
	
	def on_key_press(self, event):
		return False
		
	def on_key_release(self, event):
		return False
	
	def draw(r):
		pass 
