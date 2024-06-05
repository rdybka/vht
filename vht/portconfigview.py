# portconfigview.py - vahatraker
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

from vht import *
from vht.portconfig import *

import gi
import os

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class BoolListView(Gtk.ListBox):
    def __init__(self, lab1, lab2, tgl_func):
        super(BoolListView, self).__init__()

        self.set_selection_mode(Gtk.SelectionMode.NONE)

        self.lab1 = lab1
        self.lab2 = lab2
        self.tgl_func = tgl_func

        self.clear()

    def clear(self):
        for wdg in self.get_children():
            self.remove(wdg)

        self.head_row = Gtk.Box()
        self.head_row.set_sensitive(False)

        self.head_row.pack_start(Gtk.Label(self.lab1), False, False, 0)
        self.head_row.pack_end(Gtk.Label(self.lab2), False, False, 0)

        self.insert(self.head_row, 0)
        wdg = self.get_children()[0]
        wdg.set_sensitive(False)

    def add(self, prtname, pretty, state):
        rw = Gtk.Box()
        lb = Gtk.Label(prtname[:33])
        if pretty:
            lb.set_tooltip_markup(
                """<span font_family="Monospace" size="medium">%s</span>""" % (pretty)
            )

        rw.pack_start(lb, False, False, 0)
        statewdg = Gtk.CheckButton()
        statewdg.set_active(state)
        statewdg.connect("toggled", self.tgl_meta, prtname)
        rw.pack_end(statewdg, False, False, 0)
        self.insert(rw, -1)

    def tgl_meta(self, widget, prtname):
        if self.tgl_func:
            self.tgl_func(prtname, not widget.get_active())


class PortConfigView(Gtk.Grid):
    def __init__(self, parent):
        super(PortConfigView, self).__init__()

        self._parent = parent

        self.set_column_spacing(5)
        self.set_row_homogeneous(False)
        self.set_column_homogeneous(True)

        self.bl_in = BoolListView("inputs", "active", self.in_toggle)
        self.bl_unv_in = BoolListView("unavailable", "keep", self.in_unv_toggle)
        self.bl_out = BoolListView("outputs", "active", self.out_toggle)
        self.bl_unv_out = BoolListView("unavailable", "keep", self.out_unv_toggle)

        self.combo_out = Gtk.ComboBoxText()
        self.combo_out.connect("changed", self.on_combo_changed)
        self.combo_ignore_change = True

        self.box_in = Gtk.Box()
        self.box_in.set_orientation(Gtk.Orientation.VERTICAL)
        self.box_in.pack_start(self.bl_in, False, False, 0)
        self.box_in.pack_start(self.bl_unv_in, False, False, 0)

        self.box_out = Gtk.Box()
        self.box_out.set_orientation(Gtk.Orientation.VERTICAL)
        self.box_out.pack_start(self.bl_out, False, False, 0)
        self.box_out.pack_start(self.bl_unv_out, False, False, 0)
        self.box_out.pack_end(self.combo_out, False, False, 0)

        self.attach(self.box_in, 0, 0, 1, 1)
        self.attach(self.box_out, 1, 0, 1, 1)

        self.show_all()
        refresh_connections(mod, cfg)
        self.populate()

    def populate(self):
        self.combo_ignore_change = True
        parwin = self._parent.get_window()
        if parwin:
            parwin.freeze_updates()

        self.bl_in.clear()
        self.bl_unv_in.clear()
        self.bl_out.clear()
        self.bl_unv_out.clear()

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
                    self.bl_in.add(*[prt.name, prt.pname, inp in prt.connections])

        for p in mod.extras["portconfig"]["in"]:
            if not p in mod.ports:
                self.bl_unv_in.add(p, p, 1)

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

                    self.bl_out.add(prt.name, prt.pname, conn)

        for p in mod.extras["portconfig"]["out"][act_out]:
            if not p in mod.ports:
                self.bl_unv_out.add(p, p, 1)

        self.show_all()

        if len(self.bl_unv_out) > 1:
            self.bl_unv_out.show()
        else:
            self.bl_unv_out.hide()

        if len(self.bl_unv_in) > 1:
            self.bl_unv_in.show()
        else:
            self.bl_unv_in.hide()

        if parwin:
            parwin.thaw_updates()

        self.combo_ignore_change = False

    def on_combo_changed(self, widget):
        if self.combo_ignore_change:
            return

        self.populate()

    def in_unv_toggle(self, pname, active):
        if pname in mod.extras["portconfig"]["in"]:
            mod.extras["portconfig"]["in"].remove(pname)

        self.populate()

    def in_toggle(self, pname, active):
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

    def out_toggle(self, pname, active):
        act_out = max(0, self.combo_out.get_active())
        act_out_pname = mod.ports.output_get_name(act_out)

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

    def out_unv_toggle(self, pname, active):
        act_out = max(0, self.combo_out.get_active())

        if pname in mod.extras["portconfig"]["out"][act_out]:
            mod.extras["portconfig"]["out"][act_out].remove(pname)

        self.populate()
