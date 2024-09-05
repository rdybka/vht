# sequencelistviewpopover.py - vahatraker
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

import copy
import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gdk, Gtk, Gio

try:
    gi.require_version("GtkSource", "4")
    from gi.repository import GtkSource
except Exception:
    GtkSource = None

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

        grid2 = Gtk.Grid()

        grid = Gtk.Grid()
        grid.set_column_spacing(3)
        grid.set_row_spacing(3)
        grid.set_row_homogeneous(True)

        box = Gtk.Box()

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
        # box.pack_end(self._entry, True, True, 2)

        grid2.attach(box, 0, 1, 3, 1)

        self._trgview = SequenceTriggersView(-1, self)
        grid.attach(self._trgview, 0, 1, 3, 1)

        self._code_butt = Gtk.ToggleButton()
        self._code_butt.set_active(False)

        icon = Gio.ThemedIcon(name="system-run")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self._code_butt.add(image)
        self._code_butt.connect("clicked", self.on_code_butt_toggled)
        if GtkSource:
            box.pack_end(self._code_butt, False, False, 2)

        # self._trgview.attach(self._code_butt, 0, 3, 1, 1)

        self._run_switch = Gtk.Switch()
        self._run_switch.set_state(False)
        self._run_switch.connect("state-set", self.on_run_switch)

        if GtkSource:
            self._err_butt = Gtk.Button.new_with_label("err")
            self._err_butt.connect("clicked", self.on_err_butt_clicked)

            box.pack_end(self._err_butt, False, False, 2)
            box.pack_end(self._run_switch, False, False, 2)

        box.pack_end(self._entry, True, True, 2)
        # self._trgview.attach(self._run_switch, 5, 3, 1, 1)

        if GtkSource:
            self._textview = GtkSource.View()
            self._textview.set_monospace(True)
            self._textview.set_tab_width(4)
            self._textview.set_indent_width(4)
            self._textview.set_indent_on_tab(True)
            self._textview.set_show_line_numbers(True)
            self._textview.set_auto_indent(True)
            self._textview.set_smart_backspace(True)
            self._textview.set_insert_spaces_instead_of_tabs(True)
            tb = self._textview.get_buffer()
            tb.connect("changed", self.on_tb_changed)

            self._scroll = Gtk.ScrolledWindow()
            self._scroll.add(self._textview)
            grid.attach(self._scroll, 0, 2, 3, 2)

            self._scrollgrid = grid

        grid2.attach(grid, 0, 0, 3, 1)

        grid2.show_all()
        self.add(grid2)
        self.set_modal(False)
        self.pooped = False
        self.hide_code()
        self.curr = -1
        self._err_txt = ""
        self._hold_run = False
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

    def hide_code(self):
        if not GtkSource:
            return

        #buff = self._textview.get_buffer()
        #buff.set_text("")
        if self._scroll in self._scrollgrid:
            self._scrollgrid.remove(self._scroll)
        self._run_switch.set_state(False)
        self._run_switch.set_sensitive(False)
        self._run_switch.set_visible(False)
        self._err_butt.set_visible(False)
        self._code_butt.set_active(False)

    def show_code(self):
        if not GtkSource:
            return

        if not self._scroll in self._scrollgrid:
            self._scrollgrid.attach(self._scroll, 0, 2, 3, 2)

        self._run_switch.set_sensitive(True)
        self._run_switch.set_visible(True)

        self._code_butt.set_active(True)

        self._scrollgrid.show_all()

        buff = self._textview.get_buffer()
        if buff.get_char_count() == 0:
            buff.set_text(mod.cdaemon.def_code)

    def on_err_butt_clicked(self, butt):
        print(self._err_txt)

    def on_code_butt_toggled(self, butt):
        if butt.get_active():
            self.show_code()
        else:
            self.hide_code()
            self.time_want_to_leave = -2

    def on_run_switch(self, wdg, state):
        if not self._hold_run:
            mod.cdaemon.run(mod[self.curr], state)

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
                if self.time_want_to_leave == -2:
                    self.time_want_to_leave = 0
                else:
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

        if self.time_want_to_leave == -2:
            return True

        if self.time_want_to_leave == -1:  # closed - stop callback
            return False

        if GtkSource and self._scroll in self._scrollgrid:
            self.time_want_to_leave = 0
            return True

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
        self._hold_run = True
        self.get_window().freeze_updates()

        self._entry.set_text(mod[self.curr].extras["sequence_name"])

        if len(mod) == 1:
            self._del_button.set_sensitive(False)
        else:
            self._del_button.set_sensitive(True)

        self._trgview.seq = self.curr
        self._trgview.refresh()
        self.get_window().thaw_updates()

        if "code" in mod[self.curr].extras:
            self._textview.get_buffer().set_text(mod[self.curr].extras["code"])
            if len(mod[self.curr].extras["code"]):
                self.show_code()
                seq = mod[self.curr]
                err = mod.cdaemon.err(seq)
                if err:
                    self._err_txt = err
                    self._run_switch.set_state(False)
                    self._run_switch.set_visible(False)
                    self._err_butt.set_visible(True)
                else:
                    self._run_switch.set_visible(True)
                    self._err_butt.set_visible(False)
                    if mod.cdaemon.want_run(mod[self.curr]):
                        self._run_switch.set_state(True)

            else:
                del mod[self.curr].extras["code"]
                self.hide_code()
        else:
            self.hide_code()

        self._hold_run = False

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

    def on_tb_changed(self, tb):
        code = tb.get_text(tb.get_start_iter(), tb.get_end_iter(), False)
        if len(code) == 0 and self._hold_run:
            return

        mod[self.curr].extras["code"] = code
        r = mod.cdaemon.post_code(mod[self.curr], code)
        self._err_txt = ""

        if r:
            self._err_txt = r
            self._err_butt.set_tooltip_markup(cfg.tooltip_markup % (r))
            self._err_butt.set_visible(True)
            self._run_switch.set_state(False)
            self._run_switch.set_visible(False)
        else:
            self._run_switch.set_visible(True)
            self._err_butt.set_visible(False)
            if len(code) == 0:
                self._run_switch.set_state(False)
                self._run_switch.set_visible(False)
                # mod.cdaemon.run(mod[self.curr], False)
            else:
                self._run_switch.set_state(mod.cdaemon.want_run(mod[self.curr]))

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
