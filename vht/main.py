#!/usr/bin/env python3

# vahatraker - a live MIDI sequencer for JACK
#
# Copyright (C) 2024 Remigiusz Dybka - remigiusz.dybka@gmail.com
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

# I hereby testify,
# on Pungenday, the 29th day of Bureaucracy in the YOLD 3190,
# that everything in this program checks out with The Law of Fives

# [^^^intentionally left blank]

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk, Gio, GdkPixbuf

import sys
import os
import time
import pkg_resources

from vht.mainwin import MainWin
from vht.shortcutmayhem import ShortcutMayhem
from vht.preferenceswin import PreferencesWin
from vht.renderwin import RenderWin
from vht.codedaemon import CodeDaemon
from vht.portconfig import refresh_connections
from vht import mod, cfg, ctrlcfg, autoexec, bankcfg, randomcomposer
import vht.extras
import vht.filerotator


class VHTApp(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            application_id="io.github.rdybka.vht",
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

        action = Gio.SimpleAction.new("append", None)
        action.connect("activate", self.on_append)
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

        action = Gio.SimpleAction.new("keyb", None)
        action.connect("activate", self.on_shortcut_dialog)
        self.add_action(action)

        action = Gio.SimpleAction.new("prefs", None)
        action.connect("activate", self.on_prefs)
        self.add_action(action)

        action = Gio.SimpleAction.new("render", None)
        action.connect("activate", self.on_render)
        self.add_action(action)

    def do_command_line(self, command_line):
        self.activate()
        return 0

    def do_open(self, files, hint, n):
        self.start_load_file = files[0]
        self.activate()

    def fixfn_backup(self, lfn):
        fn = os.path.split(lfn)[1]
        if fn[0] == "~":
            fn = fn[1 : fn.rfind(".")]
            fn = os.path.join(os.path.split(lfn)[0], fn)
            return fn

        return lfn

    def do_activate(self):
        if self.start_load_file:
            try:
                mod.load(self.start_load_file)
                mod.pnq_hack = cfg.pnq_hack
                mod.inception = cfg.inception
            except FileNotFoundError:
                mod.reset()
                mod.pnq_hack = cfg.pnq_hack
                mod.inception = cfg.inception
                mod.play = cfg.start_playing
        else:
            mod.reset()
            mod.pnq_hack = cfg.pnq_hack
            mod.inception = cfg.inception
            mod.play = cfg.start_playing

        self.main_win = MainWin(self)

        self.add_window(self.main_win)
        mod.render_win_showing = False
        if mod.start_error:
            self.quit()

        if self.start_load_file:
            lfn = self.fixfn_backup(self.start_load_file.get_path())
            self.main_win.last_filename = lfn
            cfg.last_load_path = (
                "file:///" + os.path.split(self.main_win.last_filename)[0]
            )
            self.main_win.set_header_from_filename(self.main_win.last_filename)

        if not "portconfig" in mod.extras:
            pc = {}
            pc["in"] = []
            pc["out"] = {}

            for p in range(mod.max_ports):
                pc["out"][p] = []

            mod.extras["portconfig"] = pc

            if cfg.midi_default_input and cfg.midi_default_input not in pc["in"]:
                pc["in"].append(cfg.midi_default_input)

            if cfg.midi_default_output and cfg.midi_default_output not in pc["out"][0]:
                pc["out"][0].append(cfg.midi_default_output)

        refresh_connections(mod, cfg)
        mod.transport = cfg.start_transport

    def on_prefs(self, action, param):
        PreferencesWin(self.main_win, mod, cfg, self).show()

    def on_render(self, action, param):
        if not mod.render_win_showing:
            RenderWin(self.main_win, mod, cfg).show()

    def load(self, append=False):
        dialog = Gtk.FileChooserNative(
            title="Please choose a file",
            action=Gtk.FileChooserAction.OPEN,
        )

        self.add_file_filters(dialog)

        if cfg.last_load_path:
            dialog.set_current_folder_uri(cfg.last_load_path)
        elif cfg.last_save_path:
            dialog.set_current_folder_uri(cfg.last_save_path)

        response = dialog.run()

        if response == -3:
            if self.main_win.load(dialog.get_filename(), append):
                cfg.last_load_path = dialog.get_current_folder_uri()

    def on_load(self, action, param):
        self.load()

    def on_append(self, action, param):
        self.load(True)

    def on_about_dialog(self, action, param):
        ab = Gtk.AboutDialog(self.main_win)
        ab.set_license_type(Gtk.License.GPL_3_0)
        ab.set_copyright(
            "Copyright (C) 2024 Remigiusz Dybka\nremigiusz.dybka@gmail.com"
        )
        pkg = pkg_resources.require("vht")[0]
        ab.set_version(pkg.version)
        ab.set_program_name("vahatraker")
        ab.set_comments("Live MIDI sequencer")
        ab.set_logo(
            GdkPixbuf.Pixbuf.new_from_file_at_size(
                mod.data_path + os.sep + "vht.svg", 160, 160
            )
        )

        ab.run()
        ab.close()

    def on_shortcut_dialog(self, action, param):
        dlg = ShortcutMayhem()
        dlg.show()

    def autosave(self):
        if self.main_win.last_filename:
            vht.filerotator.rotate(self.main_win.last_filename, cfg.n_backups)
            ss = mod.should_save
            mod.save(self.main_win.last_filename)
            mod.saving = True
            cfg.last_save_path = cfg.last_load_path
            mod.should_save = ss

    def save_with_dialog(self):
        mod.extras["timeline_win_pos"] = (
            mod.mainwin.get_window().get_width() - mod.mainwin.hbox.get_position()
        )
        mod.extras["timeline_win_pos_y"] = mod.mainwin.timeline_box.get_position()

        if not self.main_win.last_filename:
            dialog = Gtk.FileChooserNative(
                title="Please choose a file",
                action=Gtk.FileChooserAction.SAVE,
            )

            self.add_file_filters(dialog)

            if cfg.last_save_path:
                dialog.set_current_folder_uri(cfg.last_save_path)
            elif cfg.last_load_path:
                dialog.set_current_folder_uri(cfg.last_load_path)

            response = dialog.run()

            if response == -3:
                cfg.last_save_path = dialog.get_current_folder_uri()
                fname = dialog.get_filename()

                if not fname.lower().endswith(".vht"):
                    fname += ".vht"

                self.main_win.last_filename = fname
                vht.filerotator.rotate(self.main_win.last_filename, cfg.n_backups)
                mod.save(self.main_win.last_filename)
                mod.saving = True
                self.main_win.set_header_from_filename(self.main_win.last_filename)
            return

        if self.main_win.last_filename:
            vht.filerotator.rotate(self.main_win.last_filename, cfg.n_backups)
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
    print("vahatraker %s" % (pkg.version))

    mod.start_error = None
    if mod.midi_start() != 0:
        mod.start_error = "you will need JACK for this"

    # fix local config path
    mod.cfg_path = os.path.join(GLib.get_user_config_dir(), "vht")
    if not os.path.exists(mod.cfg_path):
        print("creating", mod.cfg_path)
        os.mkdir(mod.cfg_path)

    cfg.load(os.path.join(mod.cfg_path, "config.ini"))

    mod.ctrlpr = cfg.controller_resolution
    mod.saving = False
    mod.play_mode = 0
    midig = []
    for val in cfg.midi_in.values():
        if val:
            midig.append(val)

    vht.extras.register(mod)
    mod.set_midi_record_ignore(midig)
    randomcomposer.muzakize()
    mod.cdaemon = CodeDaemon()
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

    # fix controller configs
    mod.ctrls = ctrlcfg.load()
    # fix patches
    mod.bank = bankcfg.load()
    autoexec.run()

    app = VHTApp()
    app.run(sys.argv)

    cfg.save()
    mod.play = 0
    time.sleep(0.096)
    mod.panic()
    time.sleep(0.042)
    mod.midi_stop()


if __name__ == "__main__":
    run()
