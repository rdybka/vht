#!/usr/bin/env python3
#
# Valhalla Tracker - a live MIDI sequencer for JACK
#
# Copyright (C) 2020 Remigiusz Dybka - remigiusz.dybka@gmail.com
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


from vht.mainwin import MainWin
from vht import mod, cfg, ctrlcfg, autoexec, bankcfg, randomcomposer
from gi.repository import GLib, Gtk, Gio, GdkPixbuf
import vht.extras
import sys
import os
import time
import gi
import pkg_resources

gi.require_version("Gtk", "3.0")


class VHTApp(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            application_id="com.github.rdybka.vht",
            flags=Gio.ApplicationFlags.HANDLES_OPEN | Gio.ApplicationFlags.NON_UNIQUE,
            **kwargs
        )

        self.main_win = None
        self.start_load_file = None

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

    def do_open(self, files, hint, n):
        self.start_load_file = files[0]
        self.activate()

    def do_activate(self):
        if self.start_load_file:
            if not mod.load(self.start_load_file):
                self.quit()

        self.main_win = MainWin(self)

        if mod.start_error:
            self.quit()

        if self.start_load_file:
            self.main_win.last_filename = self.start_load_file.get_path()
            cfg.last_load_path = (
                "file:///" + os.path.split(self.main_win.last_filename)[0]
            )
            self.main_win.set_header_from_filename(self.main_win.last_filename)
            self.main_win.adj.set_value(mod.bpm)

        mod.play = cfg.start_playing

    def on_load(self, action, param):
        dialog = Gtk.FileChooserDialog(
            "Please choose a file",
            self.get_active_window(),
            Gtk.FileChooserAction.OPEN,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN,
                Gtk.ResponseType.OK,
            ),
        )

        self.add_file_filters(dialog)

        if cfg.last_load_path:
            dialog.set_current_folder_uri(cfg.last_load_path)
        elif cfg.last_save_path:
            dialog.set_current_folder_uri(cfg.last_save_path)

        response = dialog.run()
        dialog.close()
        if response == Gtk.ResponseType.OK:
            if self.main_win.load(dialog.get_filename()):
                cfg.last_load_path = dialog.get_current_folder_uri()

    def on_about_dialog(self, action, param):
        ab = Gtk.AboutDialog(self.main_win)
        ab.set_license_type(Gtk.License.GPL_3_0)
        ab.set_copyright(
            "Copyright (C) 2020 Remigiusz Dybka\nremigiusz.dybka@gmail.com\n@schtixfnord"
        )
        pkg = pkg_resources.require("vht")[0]
        ab.set_version(pkg.version)
        ab.set_program_name("Valhalla Tracker")
        ab.set_comments("a live MIDI sequencer for JACK")
        ab.set_logo(
            GdkPixbuf.Pixbuf.new_from_file_at_size(
                mod.data_path + os.sep + "vht.svg", 160, 160
            )
        )
        ab.run()
        ab.close()

    def save_with_dialog(self):
        mod.extras["timeline_win_pos"] = (
            mod.mainwin.get_window().get_width() - mod.mainwin.hbox.get_position()
        )
        mod.extras["timeline_win_pos_y"] = mod.mainwin.timeline_box.get_position()

        if not self.main_win.last_filename:
            dialog = Gtk.FileChooserDialog(
                "Please choose a file",
                self.get_active_window(),
                Gtk.FileChooserAction.SAVE,
                (
                    Gtk.STOCK_CANCEL,
                    Gtk.ResponseType.CANCEL,
                    Gtk.STOCK_SAVE,
                    Gtk.ResponseType.OK,
                ),
            )

            self.add_file_filters(dialog)

            if cfg.last_save_path:
                dialog.set_current_folder_uri(cfg.last_save_path)
            elif cfg.last_load_path:
                dialog.set_current_folder_uri(cfg.last_load_path)

            response = dialog.run()

            dialog.close()
            if response == Gtk.ResponseType.OK:
                cfg.last_save_path = dialog.get_current_folder_uri()
                self.main_win.last_filename = dialog.get_filename()

                mod.save(self.main_win.last_filename)
                mod.saving = True
                self.main_win.set_header_from_filename(self.main_win.last_filename)

            return

        if self.main_win.last_filename:
            mod.save(self.main_win.last_filename)
            mod.saving = True
            cfg.last_save_path = cfg.last_load_path

    def on_save(self, action, param):
        self.save_with_dialog()

    def on_save_as(self, action, param):
        fn = self.main_win.last_filename
        self.main_win.last_filename = None
        self.save_with_dialog()
        # if cancelled
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
    if mod.midi_start() != 0:
        mod.start_error = "you will need JACK for this"

    mod.ctrlpr = cfg.controller_resolution
    mod.saving = False
    mod.play_mode = 0
    midig = []
    for val in cfg.midi_in.values():
        midig.append(tuple(val[:-1]))

    vht.extras.register(mod)
    mod.set_midi_record_ignore(midig)
    randomcomposer.muzakize()

    # fix data path
    paths2try = []

    paths2try.append(os.path.normpath(os.path.join(pkg.module_path, "data")))
    paths2try.append(os.path.normpath(os.path.join(pkg.module_path, "share/vht")))

    p = pkg.module_path
    pf = p.find("/lib")
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

    # fix controller configs
    mod.ctrls = ctrlcfg.load()
    # fix patches
    mod.bank = bankcfg.load()

    autoexec.run()

    app = VHTApp()
    app.run(sys.argv)

    mod.play = 0
    time.sleep(0.096)
    mod.panic()
    time.sleep(0.042)
    mod.midi_stop()


if __name__ == "__main__":
    run()
