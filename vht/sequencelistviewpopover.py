# sequencelistviewpopover.py - Valhalla Tracker
#
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

from vht.notebooklabel import NotebookLabel
from vht.sequencetriggersview import SequenceTriggersView
from vht.controllersview import ControllersView
from vht import cfg, mod
from gi.repository import Gdk, Gtk, Gio
from datetime import datetime
import gi

gi.require_version("Gtk", "3.0")


class SequenceListViewPopover(Gtk.Popover):
    def __init__(self, parent):
        super(SequenceListViewPopover, self).__init__()
        self.set_relative_to(parent)

        self.add_events(
            Gdk.EventMask.LEAVE_NOTIFY_MASK
            | Gdk.EventMask.ENTER_NOTIFY_MASK
            | Gdk.EventMask.BUTTON_PRESS_MASK
        )

        self.connect("leave-notify-event", self.on_leave)
        self.connect("enter-notify-event", self.on_enter)

        self._parent = parent
        self._time_want_to_leave = 0

        grid = Gtk.Grid()
        grid.set_column_spacing(3)
        grid.set_row_spacing(3)

        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="edit-delete")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.connect("clicked", self.on_remove_button_clicked)
        button.set_tooltip_markup(cfg.tooltip_markup % (cfg.key["sequence_delete"]))
        grid.attach(button, 0, 0, 1, 1)
        self._del_button = button

        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="edit-copy")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.connect("clicked", self.on_clone_button_clicked)
        button.set_tooltip_markup(cfg.tooltip_markup % (cfg.key["sequence_clone"]))
        grid.attach(button, 1, 0, 1, 1)

        self._entry = Gtk.Entry()
        self._entry.connect("changed", self.on_entry_changed)

        grid.attach(self._entry, 2, 0, 1, 1)

        self._trgview = SequenceTriggersView(-1, self)
        grid.attach(self._trgview, 0, 1, 3, 1)

        grid.show_all()
        self.add(grid)
        self.set_modal(False)
        self.pooped = False
        self.curr = -1

        # mod.gui_midi_capture = False

    def on_leave(self, wdg, prm):
        if prm.window == self.get_window():
            if prm.detail != Gdk.NotifyType.INFERIOR:
                self.time_want_to_leave = datetime.now()
        return True

    def on_enter(self, wdg, prm):
        if prm.window == self.get_window():
            self.time_want_to_leave = 0
        return True

    def tick(self, wdg, param):
        if self.time_want_to_leave == 0:  # normal
            op = self.get_opacity()
            if op < 1.0:
                self.set_opacity(op * 1.2)

            return True

        if self.time_want_to_leave == -1:  # closed - stop callback
            return False

        if self._trgview.play_mode_cb.props.popup_shown:
            self.time_want_to_leave = 0
            return True

        t = datetime.now() - self.time_want_to_leave
        t = float(t.seconds) + t.microseconds / 1000000
        if t > cfg.popup_timeout / 2.0:
            t = 1 - (t - cfg.popup_timeout / 2.0) / (cfg.popup_timeout / 2.0)
            if t > 0:
                self.set_opacity(t)
            if t < 0:
                self.hide()
                self.pooped = False
                self._trgview.capture = -1
                self._parent._menu_handle = -1
                self._parent.redraw()
                return False

        return True

    def refresh(self):
        self.get_window().freeze_updates()

        self._entry.set_text(mod.extras[self.curr][-1]["sequence_name"])

        if len(mod) == 1:
            self._del_button.set_sensitive(False)
        else:
            self._del_button.set_sensitive(True)

        self._trgview.seq = self.curr
        self._trgview.refresh()
        self.get_window().thaw_updates()

    def pop(self, curr):
        mod.clear_popups(self)
        self.set_position(Gtk.PositionType.BOTTOM)
        self.time_want_to_leave = 0
        self.set_opacity(1)
        self.add_tick_callback(self.tick)
        self.pooped = True
        self.curr = curr
        self._trgview.capture = -1
        self.refresh()
        self.show()

    def on_entry_changed(self, wdg):
        if self.curr == -1:
            return

        mod.extras[self.curr][-1]["sequence_name"] = wdg.get_text()
        self._parent.redraw()

    def on_remove_button_clicked(self, wdg):
        if self.curr == -1:
            return

        if self.curr == mod.curr_seq:
            if self.curr < len(mod) - 1:
                mod.mainwin._sequence_view.switch(mod.curr_seq + 1)
            else:
                mod.curr_seq -= 1
                mod.mainwin._sequence_view.switch(mod.curr_seq)
                self._parent.redraw()

        # move names in extras
        for r in range(self.curr, len(mod) - 1):
            mod.extras[r] = mod.extras[r + 1]

        mod.del_sequence(self.curr)
        self.hide()
        self.pooped = False
        self._parent.redraw()

    def on_clone_button_clicked(self, wdg):
        print("clone")
