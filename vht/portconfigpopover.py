# portconfigpopover.py - vahatraker
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

from vht import cfg, mod, extras
from vht.portconfigview import PortConfigView
from vht.portconfig import *
from gi.repository import Gdk, Gtk, Gio
from datetime import datetime
import gi
import copy

gi.require_version("Gtk", "3.0")


class PortConfigPopover(Gtk.Popover):
    def __init__(self, parent):
        super(PortConfigPopover, self).__init__()

        self.add_events(
            Gdk.EventMask.LEAVE_NOTIFY_MASK
            | Gdk.EventMask.ENTER_NOTIFY_MASK
            | Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
        )

        self.connect("leave-notify-event", self.on_leave)
        self.connect("enter-notify-event", self.on_enter)
        self.connect("key-press-event", self.on_key_press)

        self._parent = parent
        self._time_want_to_leave = 0

        self._cfgview = PortConfigView(self)
        self.add(self._cfgview)
        self.set_modal(False)
        self.pooped = False

        self.set_relative_to(parent)
        self.set_position(Gtk.PositionType.TOP)

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.hide()
            self.pooped = False
            return True

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
        if self._cfgview.combo_out.props.popup_shown:
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
            self.hide()
            self.pooped = False
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
                return False

        return True

    def refresh(self):
        self._cfgview.populate()

    def pop(self):
        mod.clear_popups(self)
        self.time_want_to_leave = 0
        self.set_opacity(1)
        self.add_tick_callback(self.tick)
        self.pooped = True
        self.show_all()
        self.refresh()
