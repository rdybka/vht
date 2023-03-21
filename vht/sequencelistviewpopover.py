# sequencelistviewpopover.py - vahatraker
#
# Copyright (C) 2023 Remigiusz Dybka - remigiusz.dybka@gmail.com
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

import copy
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk, Gio

from vht.notebooklabel import NotebookLabel
from vht.sequencetriggersview import SequenceTriggersView
from vht.controllersview import ControllersView
from vht import cfg, mod, extras
from datetime import datetime
from vht.poormanspiano import PoorMansPiano


class SequenceListViewPopover(Gtk.Popover):
    def __init__(self, parent):
        super(SequenceListViewPopover, self).__init__()

        self.add_events(
            Gdk.EventMask.LEAVE_NOTIFY_MASK
            | Gdk.EventMask.ENTER_NOTIFY_MASK
            | Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.SCROLL_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
        )

        self.connect("leave-notify-event", self.on_leave)
        self.connect("enter-notify-event", self.on_enter)
        self.connect("scroll-event", self.on_scroll)
        self.connect("key-press-event", self.on_key_press)

        self._parent = parent
        self._time_want_to_leave = 0
        self.pmp = PoorMansPiano(None, None)

        box = Gtk.Box()

        grid = Gtk.Grid()
        grid.set_column_spacing(3)
        grid.set_row_spacing(3)

        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="edit-delete")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.connect("clicked", self.on_remove_button_clicked)
        button.set_tooltip_markup(
            cfg.tooltip_markup2 % ("delete", cfg.key["sequence_delete"])
        )
        box.pack_start(button, False, True, 2)

        self._del_button = button

        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="edit-copy")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.connect("clicked", self.on_clone_button_clicked)
        button.set_tooltip_markup(
            cfg.tooltip_markup2 % ("clone", cfg.key["sequence_clone"])
        )
        box.pack_start(button, False, True, 2)

        self._entry = Gtk.Entry()
        self._entry.connect("changed", self.on_entry_changed)
        box.pack_end(self._entry, True, True, 2)
        grid.attach(box, 0, 0, 3, 1)

        self._trgview = SequenceTriggersView(-1, self)
        grid.attach(self._trgview, 0, 1, 3, 1)

        grid.show_all()
        self.add(grid)
        self.set_modal(False)
        self.pooped = False
        self.curr = -1

        self.set_relative_to(parent)
        self.set_position(Gtk.PositionType.LEFT)
        # mod.gui_midi_capture = False

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.hide()
            self.pooped = False
            self._trgview.capture = -1
            self._parent._menu_handle = -1
            mod.gui_midi_capture = False
            return True

        cpt = self._trgview.capture
        tv = self._trgview
        if cpt > -1:
            mnt = self.pmp.k2n(event.keyval)
            if mnt > -1:
                mod[tv.seq].set_trig(cpt, 1, 1, mnt)
                tv.refresh()

    def on_scroll(self, wdg, prm):
        last = new = self.curr
        if prm.direction == Gdk.ScrollDirection.UP:
            new -= 1

        if prm.direction == Gdk.ScrollDirection.DOWN:
            new += 1

        new = max(0, min(new, len(mod) - 1))

        if last != new:
            if new in self._parent.visible_cols:
                mod.gui_midi_capture = False
                self._trgview.capture = -1
                self.curr = new
                self.refresh()
                self._parent._menu_handle = self.curr
                self._parent.pop_point_to(self.curr)

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

        if self._trgview.mute_grp_cb.props.popup_shown:
            self.time_want_to_leave = 0
            return True

        if self._trgview.cue_grp_cb.props.popup_shown:
            self.time_want_to_leave = 0
            return True

        if self._trgview.capture > -1:
            self.time_want_to_leave = 0
            return True

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
                self.pooped = False
                self._trgview.capture = -1
                self._parent._menu_handle = -1
                mod.gui_midi_capture = False
                self._parent.redraw()
                return False

        return True

    def refresh(self):
        self.get_window().freeze_updates()

        self._entry.set_text(mod[self.curr].extras["sequence_name"])

        if len(mod) == 1:
            self._del_button.set_sensitive(False)
        else:
            self._del_button.set_sensitive(True)

        self._trgview.seq = self.curr
        self._trgview.refresh()
        self.get_window().thaw_updates()

    def unpop(self):
        self.hide()
        self.pooped = False
        self._trgview.capture = -1
        mod.gui_midi_capture = False

    def pop(self, curr):
        mod.clear_popups(self)
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

        mod[self.curr].extras["sequence_name"] = wdg.get_text()
        self._parent.redraw()

    def on_remove_button_clicked(self, wdg):
        if self.curr == -1:
            return

        if cfg.autosave_seq:
            mod.mainwin.app.autosave()

        mod.mainwin.gui_del_seq(self.curr)

        self.hide()
        self.pooped = False
        self._parent.redraw()

    def on_clone_button_clicked(self, wdg):
        seq = mod.clone_sequence(self.curr)

        seq.extras["sequence_name"] = extras.get_name(
            mod[self.curr].extras["sequence_name"]
        )

        seq.ketchup()
