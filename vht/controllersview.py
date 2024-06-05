# controllersview.py - vahatraker
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

from vht.controllereditor import ControllerEditor
from vht.controllersviewrow import ControllersViewRow
from vht import cfg, mod
from gi.repository import Gtk, Gio
import gi

gi.require_version("Gtk", "3.0")


class ControllersView(Gtk.Box):
    def __init__(self, trk, trkview, parent):
        super(ControllersView, self).__init__()

        self.set_orientation(Gtk.Orientation.VERTICAL)

        self.sw = Gtk.ScrolledWindow()

        self.parent = parent
        self.trk = trk
        self.extras = trk.extras
        self.ctrl_names = trk.extras["ctrl_names"]
        self.trkview = trkview
        self.capturing = False

        self.box = Gtk.Box()
        self.box.set_orientation(Gtk.Orientation.VERTICAL)
        self.box.set_homogeneous(False)
        self.box.set_spacing(2)

        self.sw.add(self.box)
        self.pack_start(self.sw, True, True, 0)

        self.new_ctrl = Gtk.ActionBar()

        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="list-add")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.connect("clicked", self.on_add_clicked)
        self.new_ctrl.pack_start(button)

        self.capture_button = Gtk.ToggleButton()
        self.capture_button.set_tooltip_markup(cfg.tooltip_markup % ("capture"))
        icon = Gio.ThemedIcon(name="media-record")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.capture_button.add(image)
        self.capture_button.connect("toggled", self.on_capture_toggled)
        self.new_ctrl.pack_start(self.capture_button)

        self.new_ctrl_adj = Gtk.Adjustment(1, 0, 127, 1.0, 1.0)
        self.new_ctrl_button = Gtk.SpinButton()
        self.new_ctrl_button.set_adjustment(self.new_ctrl_adj)
        self.new_ctrl_adj.set_value(1)

        self.new_ctrl_adj.connect("value-changed", self.on_new_ctrl_changed)

        self.new_ctrl.pack_start(self.new_ctrl_button)

        self.new_ctrl_entry = Gtk.Entry()

        self.new_ctrl_entry.set_text("")

        self.new_ctrl.pack_end(self.new_ctrl_entry)

        self.last_ctrl = cfg.default_ctrl_name

        # self.ctrl_names = self.extras["ctrl_names"]

        self.new_ctrl_menu = Gtk.Menu()
        i = 0
        for n, c in mod.ctrls.items():
            m = Gtk.MenuItem(n)
            sub = Gtk.Menu()
            parn = n  # parent's name
            for c, n in c.items():
                mitm = Gtk.MenuItem("%3d %s" % (c, n))
                mitm.connect("activate", self.on_menuitem_activate)
                mitm.parn = parn
                mitm.show()
                sub.append(mitm)

            sub.show()
            m.set_submenu(sub)
            m.show()

            self.new_ctrl_menu.append(m)
            i += 1

        self.new_ctrl_menu.show()
        self.new_ctrl_menu_button = Gtk.MenuButton()
        # self.new_ctrl_menu_button.connect("clicked", self.on_menu_popped)
        self.new_ctrl_menu_button.set_popup(self.new_ctrl_menu)
        self.new_ctrl.pack_end(self.new_ctrl_menu_button)

        self.pack_end(self.new_ctrl, False, False, 0)
        self.rebuild()
        self.show_all()

    def on_new_ctrl_changed(self, adj):
        c = int(adj.get_value())
        n = mod.ctrls[self.last_ctrl]
        if c in n:
            self.new_ctrl_entry.set_text(n[c].strip())
        else:
            self.new_ctrl_entry.set_text("")

    def on_menuitem_activate(self, itm):
        self.new_ctrl_adj.set_value(int(itm.get_label().split()[0]))
        self.new_ctrl_entry.set_text(itm.get_label()[3:].strip())
        self.last_ctrl = itm.parn

    def on_capture_toggled(self, wdg):
        if wdg.get_active():
            mod.gui_midi_capture = True
            self.capturing = True
            self.add_tick_callback(self.tick)
        else:
            self.capturing = False
            mod.gui_midi_capture = False

    def tick(self, wdg, param):
        if not self.capturing:
            self.capture_button.set_active(False)
            return False

        midin = mod.get_midi_in_event()

        while midin:
            if midin["type"] == 4:
                self.new_ctrl_adj.set_value(midin["note"])
            midin = mod.get_midi_in_event()

        return True

    def rebuild(self, just_gui=False):
        reuse = False

        if len(self.box.get_children()) == self.trk.nctrl - 1:
            reuse = True

        if not reuse:
            for wdg in self.box.get_children():
                self.box.remove(wdg)

        for i, c in enumerate(self.trk.ctrls):
            if c != -1:
                parn = ("", "")
                if str(i) in self.ctrl_names:
                    parn = self.ctrl_names[str(i)]
                else:
                    self.ctrl_names[str(i)] = parn

                if not reuse:
                    rw = ControllersViewRow(self, self.trk, c, i, parn[0], parn[1])
                    self.box.pack_start(rw, False, False, 0)
                else:
                    rw = self.box.get_children()[i - 1]
                    rw.ctrlnum = c
                    rw.parn = self.ctrl_names[str(i)][0]
                    name = self.ctrl_names[str(i)][1]
                    rw.ctrl_adj.set_value(self.trk.ctrl[i].ctrlnum)
                    rw.entry.set_text(name)

        for i, w in enumerate(self.box.get_children()):
            w.up_button.set_sensitive(True)
            w.down_button.set_sensitive(True)

            if i == 0:
                w.up_button.set_sensitive(False)

            if i == self.trk.nctrl - 2:
                w.down_button.set_sensitive(False)

        self.parent.refresh()

        if not just_gui:
            self.trkview.redraw_full()

        if self.get_realized():
            self.parent.parent.redraw()

    def on_add_clicked(self, wdg):
        self.trk.ctrl.add(int(self.new_ctrl_adj.get_value()))
        self.ctrl_names[str(self.trk.nctrl - 1)] = (
            self.last_ctrl,
            self.new_ctrl_entry.get_text(),
        )

        self.trk.extras.write()

        self.trkview.controller_editors.append(
            ControllerEditor(self.trkview, len(self.trk.ctrl) - 1)
        )

        self.trkview.show_controllers = True
        self.rebuild()
