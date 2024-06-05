# sequencepropviewpopover.py - vahatraker
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
import cairo
from datetime import datetime
from vht import *
from vht.trackview import TrackView

gi.require_version("Gtk", "3.0")
from gi.repository import GObject, Gdk, Gtk, Gio


class SequencePropViewPopover(Gtk.Popover):
    def __init__(self, parent, seq):
        super(SequencePropViewPopover, self).__init__()
        self.set_relative_to(parent)

        self.set_events(
            Gdk.EventMask.LEAVE_NOTIFY_MASK
            | Gdk.EventMask.ENTER_NOTIFY_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
        )

        self.connect("leave-notify-event", self.on_leave)
        self.connect("enter-notify-event", self.on_enter)
        self.connect("key-press-event", self.on_key_press)

        self.parent = parent
        self.seq = seq
        self.strip = None
        self.grid = Gtk.Grid()
        self.grid.set_column_spacing(3)
        self.grid.set_row_spacing(3)

        self.time_want_to_leave = 0

        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="list-add")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.connect("clicked", self.on_add_button_clicked)
        button.set_tooltip_markup(
            cfg.tooltip_markup2 % ("add track", cfg.key["track_add"])
        )
        self.grid.attach(button, 0, 0, 1, 1)

        self.length_adj = Gtk.Adjustment(0, 1, seq.max_length, 1.0, 1.0)
        self.length_button = Gtk.SpinButton()
        self.length_button.set_adjustment(self.length_adj)
        self.length_adj.set_value(seq.length)
        self.length_conn_id = self.length_adj.connect(
            "value-changed", self.on_length_changed
        )

        self.grid.attach(self.length_button, 1, 0, 1, 1)

        self.clone_button = Gtk.Button()
        icon = Gio.ThemedIcon(name="edit-copy")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.clone_button.add(image)
        self.clone_button.connect("clicked", self.on_clone_button_clicked)
        self.clone_button.set_tooltip_markup(
            cfg.tooltip_markup2 % ("clone", cfg.key["sequence_clone"])
        )

        self.grid.attach(self.clone_button, 0, 1, 1, 1)

        self.double_button = Gtk.Button("double")
        self.double_button.connect("clicked", self.on_double_clicked)
        self.double_button.set_tooltip_markup(
            cfg.tooltip_markup % (cfg.key["sequence_double"])
        )
        self.grid.attach(self.double_button, 1, 1, 1, 1)

        self.halve_button = Gtk.Button("halve")
        self.halve_button.connect("clicked", self.on_halve_clicked)
        self.halve_button.set_tooltip_markup(
            cfg.tooltip_markup % (cfg.key["sequence_halve"])
        )
        self.grid.attach(self.halve_button, 1, 2, 1, 1)

        self.strip_clone_button = Gtk.MenuButton()
        self.strip_clone_menu = Gtk.Menu()
        self.strip_clone_button.set_popup(self.strip_clone_menu)
        icon = Gio.ThemedIcon(name="edit-copy")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.strip_clone_button.add(image)
        txt = (
            "   make new - "
            + str(cfg.key["sequence_clone"])
            + " \nreplace top - "
            + str(cfg.key["sequence_replace"])
        )
        self.strip_clone_button.set_tooltip_markup(cfg.tooltip_markup % txt)

        m = self.strip_clone_menu
        mitm = Gtk.MenuItem("make new sequence")
        mitm.op = 1
        mitm.connect("activate", self.on_clone_menu_item_activate)
        mitm.show()
        m.append(mitm)
        mitm = Gtk.MenuItem("replace top")
        mitm.op = 2
        mitm.connect("activate", self.on_clone_menu_item_activate)
        mitm.show()
        m.append(mitm)

        self.grid.attach(self.strip_clone_button, 0, 3, 1, 1)

        self.strip_double_button = Gtk.MenuButton("double")
        self.strip_double_menu = Gtk.Menu()
        self.strip_double_button.set_popup(self.strip_double_menu)
        txt = (
            "sequence - "
            + str(cfg.key["sequence_double"])
            + " \n   strip - "
            + str(cfg.key["strip_double"])
        )
        self.strip_double_button.set_tooltip_markup(cfg.tooltip_markup % txt)
        self.grid.attach(self.strip_double_button, 1, 3, 1, 1)

        m = self.strip_double_menu
        mitm = Gtk.MenuItem("sequence")
        mitm.op = 1
        mitm.connect("activate", self.on_double_menu_item_activate)
        mitm.show()
        m.append(mitm)
        mitm = Gtk.MenuItem("strip")
        mitm.op = 2
        mitm.connect("activate", self.on_double_menu_item_activate)
        mitm.show()
        m.append(mitm)

        self.strip_halve_button = Gtk.MenuButton("halve")
        self.strip_halve_menu = Gtk.Menu()
        self.strip_halve_button.set_popup(self.strip_halve_menu)
        txt = (
            "sequence - "
            + str(cfg.key["sequence_halve"])
            + " \n   strip - "
            + str(cfg.key["strip_halve"])
        )

        self.strip_halve_button.set_tooltip_markup(cfg.tooltip_markup % txt)
        self.grid.attach(self.strip_halve_button, 1, 4, 1, 1)

        m = self.strip_halve_menu
        mitm = Gtk.MenuItem("sequence")
        mitm.op = 1
        mitm.connect("activate", self.on_halve_menu_item_activate)
        mitm.show()
        m.append(mitm)
        mitm = Gtk.MenuItem("strip")
        mitm.op = 2
        mitm.connect("activate", self.on_halve_menu_item_activate)
        mitm.show()
        m.append(mitm)

        self.grid.show_all()

        self.add(self.grid)
        self.set_modal(False)

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.hide()
            self.unpop()
            return True

    def tick(self, wdg, param):
        if self.strip_clone_menu.is_visible():
            self.time_want_to_leave = 0
            return True

        if self.strip_double_menu.is_visible():
            self.time_want_to_leave = 0
            return True

        if self.strip_halve_menu.is_visible():
            self.time_want_to_leave = 0
            return True

        if self.time_want_to_leave == 0:  # normal
            op = self.get_opacity()
            if op < 1.0:
                self.set_opacity(op * 1.2)

            return True

        if self.time_want_to_leave == -1:  # closed - stop callback
            return False

        if not cfg.popup_transition:
            self.unpop()
            return True

        t = datetime.now() - self.time_want_to_leave
        t = float(t.seconds) + t.microseconds / 1000000
        if t > cfg.popup_timeout / 2.0:
            t = 1 - (t - cfg.popup_timeout / 2.0) / (cfg.popup_timeout / 2.0)
            if t > 0:
                self.set_opacity(t)
            if t < 0:
                self.hide()
                self.unpop()

        return True

    def on_length_changed(self, adj):
        val = int(adj.get_value())
        if self.seq.length == val:
            return

        ed = None
        if mod.active_track:
            ed = mod.active_track.edit
        if ed and val <= ed[1]:
            TrackView.leave_all()

        self.seq.length = val
        for trk in self.seq:
            if trk.nsrows > self.seq.length:
                trk.nsrows = self.seq.length

        adj.set_value(self.seq.length)

        self.parent.seqview.recalculate_row_spacing()
        self.parent.seqview.redraw_track()
        self.parent.seqview.queue_draw()

    def on_leave(self, wdg, prm):
        if prm.window == self.get_window():
            if prm.detail != Gdk.NotifyType.INFERIOR:
                if self.time_want_to_leave == 0:
                    self.time_want_to_leave = datetime.now()
        return True

    def on_enter(self, wdg, prm):
        if prm.window == self.get_window():
            self.time_want_to_leave = 0
        return True

    def unpop(self):
        self.hide()
        self.time_want_to_leave = -1
        self.parent.popped = False
        self.parent.button_highlight = False
        self.parent.redraw()

    def on_add_button_clicked(self, switch):
        self.parent.add_track()
        self.parent.seqview.recalculate_row_spacing()

    def on_clone_button_clicked(self, switch):
        idx = mod.clone_sequence(self.seq.index).index

        mod[idx].extras["sequence_name"] = extras.get_name(
            mod[self.seq.index].extras["sequence_name"]
        )

    def on_double_clicked(self, switch):
        self.parent.seqview.double()
        self.length_adj.set_value(self.seq.length)

    def on_halve_clicked(self, switch):
        self.parent.seqview.halve()
        self.length_adj.set_value(self.seq.length)

    def pop(self):
        mod.clear_popups(self)
        self.length_adj.set_value(self.seq.length)
        self.strip = None
        if type(self.seq.index) is tuple:
            self.strip = mod.timeline.strips[self.seq.index[1]]

        if self.strip:
            self.clone_button.hide()
            self.double_button.hide()
            self.halve_button.hide()
            self.strip_clone_button.show()
            self.strip_double_button.show()
            self.strip_halve_button.show()
        else:
            self.clone_button.show()
            self.double_button.show()
            self.halve_button.show()
            self.strip_clone_button.hide()
            self.strip_double_button.hide()
            self.strip_halve_button.hide()

        self.time_want_to_leave = 0
        self.add_tick_callback(self.tick)
        self.show()

    def on_clone_menu_item_activate(self, itm):
        if itm.op == 1:
            idx = mod.clone_sequence(self.seq.index).index

            mod[idx].extras["sequence_name"] = extras.get_name(
                mod[self.seq.index].extras["sequence_name"]
            )
            self.unpop()
            return

        if itm.op == 2:
            mod.replace_sequence(self.strip.seq.index[1])
            self.unpop()
            return

    def on_double_menu_item_activate(self, itm):
        if itm.op == 1:
            self.parent.seqview.double()
            self.length_adj.set_value(self.seq.length)
            return

        if itm.op == 2:
            self.strip.double()
            return

    def on_halve_menu_item_activate(self, itm):
        if itm.op == 1:
            self.parent.seqview.halve()
            self.length_adj.set_value(self.seq.length)
            return

        if itm.op == 2:
            self.strip.halve()
            return
