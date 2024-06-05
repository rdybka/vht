# renderwin.py - vahatraker
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


import gi
import os

from vht.portconfig import refresh_connections

gi.require_version("Gtk", "3.0")

from gi.repository import GLib, Gtk, Gdk


class RenderWin(Gtk.Window):
    def __init__(self, parent, mod, cfg):
        super(RenderWin, self).__init__()

        self.cfg = cfg
        self.mod = mod
        self.parent = parent
        self.mod.render_win_showing = True
        self.allow_exit = True
        self.capturing = False
        self.rend = mod.renderer

        self.set_transient_for(self.parent)
        self.set_resizable(False)

        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", self.on_destroy)

        self.hb = Gtk.HeaderBar()
        self.hb.set_title("Render")
        self.hb.set_show_close_button(True)
        self.set_titlebar(self.hb)

        self.hb.show_all()

        self.grid = Gtk.Grid()

        labx = 0.8
        lab = Gtk.Label.new("mode:")
        lab.set_xalign(labx)
        self.grid.attach(lab, 0, 0, 1, 1)

        self.mode_cmb = Gtk.ComboBoxText()
        self.mode_cmb.append_text("Sequence")
        self.mode_cmb.append_text("Timeline")
        self.mode_cmb.append_text("Live")
        self.mode_cmb.append_text("What u'd hear")
        self.mode_cmb.connect("changed", self.on_mode_cmb_changed)

        self.grid.attach(self.mode_cmb, 1, 0, 2, 1)

        lab = Gtk.Label.new("format:")
        lab.set_xalign(labx)
        self.grid.attach(lab, 0, 1, 1, 1)
        self.format_cmb = Gtk.ComboBoxText()

        self.formats = ["wav", "flac", "ogg"]
        for f in self.formats:
            self.format_cmb.append_text(f)

        self.format_cmb.connect("changed", self.on_format_cmb_changed)

        if cfg.render_format in self.formats:
            self.format_cmb.set_active(self.formats.index(cfg.render_format))
        else:
            self.format_cmb.set_active(0)

        self.grid.attach(self.format_cmb, 1, 1, 2, 1)

        self.midi_sw = Gtk.Switch()
        self.midi_sw.set_active(cfg.render_midi)
        self.midi_sw.connect("state-set", self.on_midi_switch)

        lab = Gtk.Label.new("midi:")
        bx = Gtk.Box()
        bx.pack_start(lab, False, False, 0)
        bx.pack_end(self.midi_sw, False, False, 0)
        self.grid.attach(bx, 2, 2, 1, 1)

        lab = Gtk.Label.new("dest:")
        lab.set_xalign(labx)
        self.grid.attach(lab, 0, 3, 1, 1)

        self.butt_fc = Gtk.FileChooserButton.new(
            "select output folder", Gtk.FileChooserAction.SELECT_FOLDER
        )
        self.butt_fc.connect("file-set", self.on_folder_set)
        self.butt_fc.set_current_folder(cfg.render_folder)
        self.grid.attach(self.butt_fc, 1, 3, 2, 1)

        lab = Gtk.Label.new("silence:")
        lab.set_xalign(labx)
        self.grid.attach(lab, 0, 4, 1, 1)

        box = Gtk.Box()
        self.secs_adj = Gtk.Adjustment(0, 0, 123, 1.0, 1.0)
        self.secs_button = Gtk.SpinButton()
        self.secs_button.set_adjustment(self.secs_adj)
        self.secs_adj.set_value(cfg.render_secs)
        self.secs_adj.connect("value-changed", self.on_secs_changed)
        self.grid.attach(self.secs_button, 1, 4, 2, 1)

        lab = Gtk.Label.new("meter:")
        lab.set_xalign(labx)
        self.grid.attach(lab, 0, 5, 1, 1)

        self.meter_cmb = Gtk.ComboBoxText()
        self.meters = ["none", "vu", "ppm", "dpm", "jf", "sco"]
        for f in self.meters:
            self.meter_cmb.append_text(f)

        self.meter_cmb.set_active(cfg.render_meter)
        self.meter_cmb.connect("changed", self.on_meter_cmb_changed)

        self.grid.attach(self.meter_cmb, 1, 5, 2, 1)

        self.rbutt = Gtk.Button()
        self.rbutt.set_label("Start!")
        self.rbutt.connect("clicked", self.on_go_clicked)
        self.grid.attach(self.rbutt, 2, 7, 1, 1)

        self.progress = Gtk.ProgressBar()
        self.grid.attach(self.progress, 0, 6, 3, 1)

        self.mode_cmb.set_active(cfg.render_mode)

        if not mod.renderer.available:
            self.rbutt.set_sensitive(False)
            self.rbutt.set_label("jack_capture not found")

        self.add(self.grid)
        self.show_all()

    def exit_on(self):
        self.allow_exit = True
        self.hb.set_show_close_button(True)
        self.set_modal(False)

    def exit_off(self):
        self.allow_exit = False
        self.hb.set_show_close_button(False)

    def on_folder_set(self, wdg):
        self.cfg.render_folder = wdg.get_filename()

    def on_meter_cmb_changed(self, wdg):
        self.cfg.render_meter = wdg.get_active()

    def on_midi_switch(self, wdg, prm):
        self.cfg.render_midi = prm

    def on_mode_cmb_changed(self, wdg):
        self.cfg.render_mode = wdg.get_active()
        if self.cfg.render_mode == 2:
            self.secs_button.set_sensitive(False)
            self.meter_cmb.set_sensitive(True)
        else:
            self.secs_button.set_sensitive(True)
            self.meter_cmb.set_sensitive(False)

        if self.cfg.render_mode == 3:
            self.secs_button.set_sensitive(False)
            self.meter_cmb.set_sensitive(False)

    def on_format_cmb_changed(self, wdg):
        self.cfg.render_format = wdg.get_active_text()

    def on_secs_changed(self, adj):
        s = int(adj.get_value())
        self.cfg.render_secs = s

    def on_go_clicked(self, wdg):
        fnm = self.mod.mainwin.hb.get_title()
        if not fnm:
            fnm = "untitled_masterpiece"

        if not self.capturing:
            self.capturing = True
            self.exit_off()

            if self.cfg.render_mode == 3:
                self.rend.start_wudh(
                    self.cfg.render_folder,
                    fnm,
                    self.cfg.render_format,
                    self.cfg.render_meter,
                )

                wdg.set_label("Stop")
                self.mod.mainwin.timeline_view.follow = True

            if self.cfg.render_mode == 2:
                self.rend.start_live(
                    self.cfg.render_folder,
                    fnm,
                    self.cfg.render_format,
                    self.cfg.render_meter,
                )

                wdg.set_label("Stop")

            if self.cfg.render_mode == 1:
                self.rend.start_timeline(
                    self.cfg.render_folder,
                    fnm,
                    self.cfg.render_format,
                    self.cfg.render_secs,
                )

                self.set_modal(True)
                wdg.set_label("Stop")
                self.mod.mainwin.timeline_view.follow = True
                # wdg.set_sensitive(False)

            if self.cfg.render_mode == 0:
                self.rend.start_sequence(
                    self.cfg.render_folder,
                    fnm,
                    self.cfg.render_format,
                    self.cfg.render_secs,
                )

                self.set_modal(True)
                wdg.set_label("Working")
                wdg.set_sensitive(False)

            self.add_tick_callback(self.tick)

            self.secs_button.set_sensitive(False)
            self.butt_fc.set_sensitive(False)
            self.format_cmb.set_sensitive(False)
            self.mode_cmb.set_sensitive(False)
            self.meter_cmb.set_sensitive(False)
            return

        self.capturing = False
        self.exit_on()

        wdg.set_label("Start")

        if self.cfg.render_mode < 2:
            self.secs_button.set_sensitive(True)
            self.meter_cmb.set_sensitive(False)
        else:
            self.meter_cmb.set_sensitive(True)

        if self.cfg.render_mode == 3:
            self.secs_button.set_sensitive(False)
            self.meter_cmb.set_sensitive(False)

        self.butt_fc.set_sensitive(True)
        self.format_cmb.set_sensitive(True)
        self.mode_cmb.set_sensitive(True)
        self.rend.stop()

    def tick(self, wdg, param):
        if not self.capturing:
            self.progress.set_fraction(0)
            return False

        if self.rend.running:
            self.progress.pulse()

        if self.rend.finished:
            self.exit_on()
            self.capturing = False
            self.rbutt.set_label("Start")
            self.rbutt.set_sensitive(True)

            if self.cfg.render_mode < 2:
                self.secs_button.set_sensitive(True)
                self.meter_cmb.set_sensitive(False)
            else:
                self.meter_cmb.set_sensitive(True)

            self.butt_fc.set_sensitive(True)
            self.format_cmb.set_sensitive(True)
            self.mode_cmb.set_sensitive(True)

        return True

    def on_destroy(self, wdg):
        self.mod.render_win_showing = False
        return

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            if self.allow_exit:
                self.destroy()
            return True
