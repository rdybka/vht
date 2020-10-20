# preferenceswin.py - Valhalla Tracker
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

import gi
import os

from vht.notebooklabel import NotebookLabel

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, Gdk


class PreferencesWin(Gtk.Window):
    def __init__(self, parent, cfg):
        super(PreferencesWin, self).__init__()
        self.cfg = cfg
        self.parent = parent

        self.set_transient_for(self.parent)
        self.set_resizable(False)
        self.set_modal(True)

        self.connect("key-press-event", self.on_key_press)

        self.hb = Gtk.HeaderBar()
        self.hb.set_title("Preferences")
        self.hb.set_show_close_button(True)
        self.set_titlebar(self.hb)
        self.hb.show_all()
        self.refresh()

        self.nb = Gtk.Notebook()

        self.box1 = self.create_box1()
        self.box2 = self.create_box2()
        self.box3 = self.create_box3()

        self.nb.append_page(self.box1, NotebookLabel("Look & Feel", self.nb, 0))
        self.nb.append_page(self.box2, NotebookLabel("Defaults", self.nb, 1))
        self.nb.append_page(self.box3, NotebookLabel("MIDI", self.nb, 2))

        self.add(self.nb)
        self.show_all()

    def refresh(self):
        pass

    def create_box1(self):
        gr = Gtk.Grid()
        mrg = 5
        gr.set_margin_top(mrg)
        gr.set_margin_bottom(mrg)
        gr.set_margin_left(mrg)
        gr.set_margin_right(mrg)

        gr.attach(Gtk.Label(label="Sequence:"), 0, 0, 2, 1)
        cbutt = Gtk.ColorButton()
        cbutt.set_use_alpha(False)
        cbutt.set_rgba(Gdk.RGBA(*self.cfg.colour, 1))
        cbutt.connect("notify::rgba", self.on_colour_activated, 0)
        fbutt = Gtk.FontButton()
        fbutt.set_font("%s %d" % (self.cfg.seq_font, self.cfg.seq_font_size))
        fbutt.connect("notify::font", self.on_font_activated, 0)
        gr.attach(cbutt, 1, 1, 1, 1)
        gr.attach(fbutt, 2, 1, 1, 1)

        return gr

    def create_box2(self):
        gr = Gtk.Grid()
        return gr

    def create_box3(self):
        gr = Gtk.Grid()
        return gr

    def on_colour_activated(self, wdg, prm, data):
        if data == 0:
            rgba = wdg.get_rgba()
            self.cfg.colour = (rgba.red, rgba.green, rgba.blue)
            self.parent.sequence_view.zoom(1)
            self.parent.sequence_view.zoom(-1)

    def on_font_activated(self, wdg, prm, data):
        if data == 0:
            face = wdg.get_font_face()
            fdesc = wdg.get_font_desc()
            sz = wdg.get_font_size() // 1000
            self.cfg.seq_font = "%s %s" % (fdesc.get_family(), face.get_face_name())
            # self.cfg.seq_font_size = sz
            print(self.cfg.seq_font, self.cfg.seq_font_size)
            self.parent.sequence_view.zoom(1)
            self.parent.sequence_view.zoom(-1)

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
            return True
