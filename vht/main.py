#!/usr/bin/env python3
#
# Valhalla Tracker
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
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, Gio

from vht import *
from vht import randomcomposer
from vht.mainwin import MainWin

class VHTApp(Gtk.Application):
	def __init__(self):
		Gtk.Application.__init__(self, application_id = "com.github.rdybka.vht", 
			flags = Gio.ApplicationFlags.NON_UNIQUE)
			
	def do_startup(self):
		Gtk.Application.do_startup(self)
		
		action = Gio.SimpleAction.new("quit", None)
		action.connect("activate", self.on_quit)
		self.add_action(action)

		action = Gio.SimpleAction.new("load", None)
		action.connect("activate", self.on_load)
		self.add_action(action)

		action = Gio.SimpleAction.new("save", None)
		action.connect("activate", self.on_save)
		self.add_action(action)

		action = Gio.SimpleAction.new("save_as", None)
		action.connect("activate", self.on_save_as)
		self.add_action(action)


		builder = Gtk.Builder.new_from_string(MENU_XML, -1)
		self.set_app_menu(builder.get_object("app-menu"))

	def do_activate(self):
		win = MainWin(self)
		
		if mod.start_error:
			self.quit()
			
		self.add_window(win)
		win.show_all()
		mod.play = True
		
	def on_quit(self, action, param):
		self.quit()

	def on_load(self, action, param):
		print("load")
	
	def on_save(self, action, param):
		print(mod.to_xml())
	
	def on_save_as(self, action, param):
		print("save_as")
	

def run():
	mod.start_error = None
	if mod.jack_start() != 0:
		mod.start_error = "you will need JACK for this"

	#mod.dump_notes = True
	randomcomposer.muzakize()
	#print(mod.to_xml())
	try:
		app = VHTApp()

		app.run(sys.argv)
	except:
		mod.jack_stop()	
		sys.exit()

	# is this reliable? should we wait for module.mute == 0?
	mod.play = False
	mod.jack_stop()
	
if __name__ == "__main__":
	run()

MENU_XML="""
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <menu id="app-menu">
    <section>
	<item>
        <attribute name="action">app.load</attribute>
        <attribute name="label">_Load</attribute>
      </item>
      <item>
        <attribute name="action">app.save</attribute>
        <attribute name="label">_Save</attribute>
      </item>
      <item>
        <attribute name="action">app.save_as</attribute>
        <attribute name="label">Save as</attribute>
      </item>
      
    </section>
    <section>
      <item>
        <attribute name="action">app.prefs</attribute>
        <attribute name="label">_Preferences</attribute>
      </item>
    
    </section>
    <section>
      
      <item>
        <attribute name="action">app.about</attribute>
        <attribute name="label">_About</attribute>
      </item>
      <item>
        <attribute name="action">app.quit</attribute>
        <attribute name="label">_Quit</attribute>
        <attribute name="accel">&lt;Primary&gt;q</attribute>
    </item>
    </section>
  </menu>
</interface>
"""
