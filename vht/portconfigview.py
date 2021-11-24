# portconfigview.py - vahatraker
#
# Copyright (C) 2021 Remigiusz Dybka - remigiusz.dybka@gmail.com
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

from vht import *
from vht.portconfig import *

import gi
import os

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class PortConfigView(Gtk.Grid):
    def __init__(self, parent):
        super(PortConfigView, self).__init__()

        self._parent = parent

        self.set_column_spacing(5)
        self.set_row_homogeneous(False)
        self.set_column_homogeneous(True)

        self.store_in = Gtk.ListStore(str, bool)
        self.store_out = Gtk.ListStore(str, bool)
        self.store_unv_in = Gtk.ListStore(str, bool)
        self.store_unv_out = Gtk.ListStore(str, bool)

        self.tv_in = Gtk.TreeView(self.store_in)
        rendtxt = Gtk.CellRendererText()
        rend_in_toggle = Gtk.CellRendererToggle()
        rend_in_toggle.connect("toggled", self.on_input_toggled)
        in_col1 = Gtk.TreeViewColumn("inputs", rendtxt, text=0)
        in_col2 = Gtk.TreeViewColumn("active", rend_in_toggle, active=True)
        self.tv_in.append_column(in_col1)
        self.tv_in.append_column(in_col2)

        self.tv_unv_in = Gtk.TreeView(self.store_unv_in)
        rend_unv_in_toggle = Gtk.CellRendererToggle()
        rend_unv_in_toggle.connect("toggled", self.on_unv_input_toggled)
        in_unv_col1 = Gtk.TreeViewColumn("unavailable", rendtxt, text=0)
        in_unv_col2 = Gtk.TreeViewColumn("keep", rend_unv_in_toggle, active=True)
        self.tv_unv_in.append_column(in_unv_col1)
        self.tv_unv_in.append_column(in_unv_col2)

        self.tv_out = Gtk.TreeView(self.store_out)
        rend_out_toggle = Gtk.CellRendererToggle()
        rend_out_toggle.connect("toggled", self.on_output_toggled)
        out_col1 = Gtk.TreeViewColumn("outputs", rendtxt, text=0)
        out_col2 = Gtk.TreeViewColumn("active", rend_out_toggle, active=True)
        self.tv_out.append_column(out_col1)
        self.tv_out.append_column(out_col2)

        self.tv_unv_out = Gtk.TreeView(self.store_unv_out)
        rend_out_toggle = Gtk.CellRendererToggle()
        rend_out_toggle.connect("toggled", self.on_unv_output_toggled)
        out_col1 = Gtk.TreeViewColumn("unavailable", rendtxt, text=0)
        out_col2 = Gtk.TreeViewColumn("keep", rend_out_toggle, active=True)
        self.tv_unv_out.append_column(out_col1)
        self.tv_unv_out.append_column(out_col2)

        self.combo_out = Gtk.ComboBoxText()
        self.combo_out.connect("changed", self.on_combo_changed)
        self.combo_ignore_change = True

        self.box_out = Gtk.Box()
        self.box_out.set_orientation(Gtk.Orientation.VERTICAL)
        self.box_out.pack_start(self.combo_out, False, False, 0)
        self.box_out.pack_start(self.tv_out, False, False, 0)
        self.box_out.pack_start(self.tv_unv_out, False, False, 0)

        self.attach(self.tv_in, 0, 0, 1, 1)
        self.attach(self.box_out, 1, 0, 1, 1)
        self.attach(self.tv_unv_in, 0, 1, 1, 1)

        self.show_all()
        refresh_connections(mod, cfg)
        self.populate()

    def populate(self):
        self.combo_ignore_change = True
        parwin = self._parent.get_window()
        if parwin:
            parwin.freeze_updates()

        self.store_in.clear()
        self.store_unv_in.clear()
        self.store_out.clear()
        self.store_unv_out.clear()

        act_out = max(0, self.combo_out.get_active())
        self.combo_out.remove_all()

        for p in range(mod.max_ports):
            self.combo_out.append_text(
                "port %02d %s" % (p, "[open]" if mod.ports.output_is_open(p) else "")
            )

        self.combo_out.set_active(act_out)

        # inputs

        inp = None
        outp = None
        mod.ports.refresh()

        for prt in mod.ports:
            if prt.mine and prt.input:
                inp = prt

        for prt in mod.ports:
            if prt.type == "midi" and not prt.mine:
                if prt.output:
                    self.store_in.append([prt.name, inp in prt.connections])

        for p in mod.extras["portconfig"]["in"]:
            if not p in mod.ports:
                self.store_unv_in.append([p, 1])

        if len(self.store_unv_in):
            self.tv_unv_in.show()
        else:
            self.tv_unv_in.hide()

        # outputs
        inp = None
        outp = None

        for prt in mod.ports:
            if prt.mine and prt.output:
                if act_out == int(prt.name[-2:]):
                    inp = prt

        for prt in mod.ports:
            if prt.type == "midi" and not prt.mine:
                if prt.input:
                    conn = False
                    if inp and inp in prt.connections:
                        conn = True

                    self.store_out.append([prt.name, conn])

        for p in mod.extras["portconfig"]["out"][act_out]:
            if not p in mod.ports:
                self.store_unv_out.append([p, 1])

        if len(self.store_unv_out):
            self.tv_unv_out.show()
        else:
            self.tv_unv_out.hide()

        if parwin:
            parwin.thaw_updates()

        self.combo_ignore_change = False

    def on_combo_changed(self, widget):
        if self.combo_ignore_change:
            return

        self.populate()

    def on_unv_input_toggled(self, widget, path):
        pname = self.store_unv_in[path][0]
        if pname in mod.extras["portconfig"]["in"]:
            mod.extras["portconfig"]["in"].remove(pname)

        self.populate()

    def on_input_toggled(self, widget, path):
        pname = self.store_in[path][0]
        active = self.store_in[path][1]

        if pname not in mod.extras["portconfig"]["in"]:
            mod.extras["portconfig"]["in"].append(pname)

        pfrom = None
        pto = None

        for p in mod.ports:
            if p.name == pname:
                pfrom = p
            if p.mine and p.input:
                pto = p

        if pfrom and pto:
            if active:
                pfrom.disconnect(pto)
                if pname in mod.extras["portconfig"]["in"]:
                    mod.extras["portconfig"]["in"].remove(pname)

        refresh_connections(mod, cfg)
        self.populate()

    def on_output_toggled(self, widget, path):
        pname = self.store_out[path][0]
        act_out = max(0, self.combo_out.get_active())
        act_out_pname = mod.ports.output_get_name(act_out)
        active = self.store_out[path][1]

        if not active:
            if pname not in mod.extras["portconfig"]["out"][act_out]:
                mod.extras["portconfig"]["out"][act_out].append(pname)

        active = not active

        pfrom = None
        pto = None

        for p in mod.ports:
            if p.name == pname:
                pto = p
            if p.mine and p.output and p.name == act_out_pname:
                pfrom = p

        if not active:
            if pfrom and pto:
                pfrom.disconnect(pto)

            if pname in mod.extras["portconfig"]["out"][act_out]:
                mod.extras["portconfig"]["out"][act_out].remove(pname)

        refresh_connections(mod, cfg)
        self.populate()

    def on_unv_output_toggled(self, widget, path):
        act_out = max(0, self.combo_out.get_active())
        pname = self.store_unv_out[path][0]
        if pname in mod.extras["portconfig"]["out"][act_out]:
            mod.extras["portconfig"]["out"][act_out].remove(pname)

        self.populate()
