#!/usr/bin/env python3
#
# Valhalla Tracker - a live MIDI sequencer for JACK
# Copyright (C) 2019 Remigiusz Dybka - remigiusz.dybka@gmail.com
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
import pkg_resources

gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, Gio, GdkPixbuf

from vht import mod, cfg, ctrlcfg, bankcfg, randomcomposer
from vht.mainwin import MainWin

class VHTApp(Gtk.Application):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, application_id = "com.github.rdybka.vht",
			flags = Gio.ApplicationFlags.HANDLES_COMMAND_LINE |\
			Gio.ApplicationFlags.NON_UNIQUE, **kwargs)

		self.main_win = None

	def do_startup(self):
		Gtk.Application.do_startup(self)

		action = Gio.SimpleAction.new("load", None)
		action.connect("activate", self.on_load)
		self.add_action(action)

		action = Gio.SimpleAction.new("save", None)
		action.connect("activate", self.on_save)
		self.add_action(action)

		action = Gio.SimpleAction.new("save_as", None)
		action.connect("activate", self.on_save_as)
		self.add_action(action)

		action = Gio.SimpleAction.new("about", None)
		action.connect("activate", self.on_about_dialog)
		self.add_action(action)

	def do_command_line(self, command_line):
		self.activate()
		return 0

	def do_activate(self):
		self.main_win = MainWin(self)

		if mod.start_error:
			self.quit()

		self.add_window(self.main_win)
		self.main_win.show_all()

		mod.play = True

	def on_quit(self, action, param):
		self.quit()

	def on_load(self, action, param):
		dialog = Gtk.FileChooserDialog("Please choose a file", self.get_active_window(),
			Gtk.FileChooserAction.OPEN,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

		self.add_file_filters(dialog)

		response = dialog.run()
		dialog.close()
		if response == Gtk.ResponseType.OK:
			self.main_win.load(dialog.get_filename())

	def on_about_dialog(self, action, param):
		ab = Gtk.AboutDialog(self.main_win)
		ab.set_license_type(Gtk.License.GPL_3_0)
		ab.set_copyright("Copyright (C) 2019 Remigiusz Dybka\nremigiusz.dybka@gmail.com\n@schtixfnord")
		pkg = pkg_resources.require("vht")[0]
		ab.set_version(pkg.version)
		ab.set_program_name("Valhalla Tracker")
		ab.set_comments("a live MIDI sequencer for JACK")
		ab.set_logo(GdkPixbuf.Pixbuf.new_from_file_at_size(mod.data_path + os.sep + "vht.svg", 160, 160))
		ab.run()
		ab.close()

	def save_with_dialog(self):
		if not self.main_win.last_filename:
			dialog = Gtk.FileChooserDialog("Please choose a file", self.get_active_window(),
				Gtk.FileChooserAction.SAVE,
				(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
				Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

			self.add_file_filters(dialog)

			response = dialog.run()
			dialog.close()
			if response == Gtk.ResponseType.OK:
				self.main_win.last_filename = dialog.get_filename()
				mod.save(self.main_win.last_filename)
				self.main_win.hb.set_title(self.main_win.last_filename)

			return

		if self.main_win.last_filename:
			mod.save(self.main_win.last_filename)

	def on_save(self, action, param):
		self.save_with_dialog()

	def on_save_as(self, action, param):
		fn = self.main_win.last_filename
		self.main_win.last_filename = None
		self.save_with_dialog()
		if not self.main_win.last_filename:
			self.main_win.last_filename = fn

	def add_file_filters(self, dialog):
		filter_vht = Gtk.FileFilter()
		filter_vht.set_name("vht module")
		filter_vht.add_pattern("*.vht")
		dialog.add_filter(filter_vht)

		filter_any = Gtk.FileFilter()
		filter_any.set_name("Any files")
		filter_any.add_pattern("*")
		dialog.add_filter(filter_any)

def run():
	pkg = pkg_resources.require("vht")[0]
	print("Valhalla Tracker %s" % (pkg.version))

	mod.start_error = None
	if mod.jack_start() != 0:
		mod.start_error = "you will need JACK for this"

	mod.ctrlpr = cfg.controller_resolution

	#mod.dump_notes = True
	midig = []
	for val in cfg.midi_in.values():
		midig.append(tuple(val[:-1]))

	mod.set_midi_record_ignore(midig)
	randomcomposer.muzakize()

	# fix data path
	paths2try = []

	paths2try.append(os.path.normpath(os.path.join(pkg.module_path, "data")))
	paths2try.append(os.path.normpath(os.path.join(pkg.module_path, "share/vht")))

	p = pkg.module_path
	pf = p.find('/lib')
	if pf:
		p = p[:pf]

		paths2try.append(os.path.normpath(os.path.join(p, "share/vht")))

	mod.data_path = "."

	for p in paths2try:
		if os.path.exists(p):
			mod.data_path = p

	# fix local config path
	mod.cfg_path = os.path.expanduser("~/.config/vht")
	if not os.path.exists(mod.cfg_path):
		print("creating", mod.cfg_path)
		os.mkdir(mod.cfg_path)

	#print("data:", mod.data_path)
	#print("cfg:", mod.cfg_path)

	# fix controller configs
	mod.ctrls = ctrlcfg.load()
	# fix patches
	mod.bank = bankcfg.load()

	#print(mod.to_xml())
	try:
		app = VHTApp()
		app.run(sys.argv)
	except:
		mod.jack_stop()
		sys.exit()

	mod.play = False
	mod.jack_stop()


if __name__ == "__main__":
	run()
