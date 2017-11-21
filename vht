#!/usr/bin/env python3

# Poor Man's Sequencer
#
# Copyright (C) 2017 Remigiusz Dybka
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys, os

sys.path.append("src")

try:
	from libvht import vht
except ImportError:
	sys.path.append(__file__.replace("/bin/vht", "/share/vht"))
	

from libvht import vht

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, Gio

from mainwin import *
import randomcomposer
import vhtcfg

class VHTApp(Gtk.Application):
	def __init__(self):
		Gtk.Application.__init__(self, application_id = "com.github.rdybka.vht", 
			flags = Gio.ApplicationFlags.NON_UNIQUE)
		
	def do_activate(self):
		win = MainWin(self)
		
		if vht.start_error:
			self.quit()
			
		self.add_window(win)
		win.show_all()
		vht.play = True

if __name__ == "__main__":
	vht.start_error = None
	if vht.jack_start() != 0:
		vht.start_error = "you will need JACK for this"

	# move this stuff to proper configuration
	vht.cfg = vhtcfg.cfg()
	vht.nports = 3
	
	randomcomposer.muzakize()

	try:
		app = VHTApp()

		app.run(sys.argv)
	except:
		vht.jack_stop()	
		sys.exit()

	# is this reliable? should we wait for module.mute == 0?
	vht.play = False
	
	vht.jack_stop()
