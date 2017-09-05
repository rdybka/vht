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

import pms
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gio
from gi.repository import Gtk

from mainwin import *

class PmsApp(Gtk.Application):
	def __init__(self):
		Gtk.Application.__init__(self, application_id = "com.github.rdybka.pms", 
			flags = Gio.ApplicationFlags.FLAGS_NONE)
	
	def do_activate(self):
		win = Pms_MainWin(pms, self)
		win.show_all()

if __name__ == "__main__":
	if pms.start() != 0: 
		exit()
	
	app = PmsApp()
	app.run(sys.argv)

	pms.stop()

