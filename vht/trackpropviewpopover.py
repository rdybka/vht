# trackpropviewpopover.py - vahatraker
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

from vht.notebooklabel import NotebookLabel
from vht.controllersview import ControllersView
from vht.mandymenu import MandyMenu
from vht import cfg, mod
from gi.repository import Gdk, Gtk, Gio
from datetime import datetime
import gi
import copy

gi.require_version("Gtk", "3.0")


class TrackPropViewPopover(Gtk.Popover):
    def __init__(self, parent, trk):
        super(TrackPropViewPopover, self).__init__()
        self.set_relative_to(parent)

        self.add_events(
            Gdk.EventMask.LEAVE_NOTIFY_MASK
            | Gdk.EventMask.ENTER_NOTIFY_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
            | Gdk.EventMask.SCROLL_MASK
        )

        self.connect("leave-notify-event", self.on_leave)
        self.connect("enter-notify-event", self.on_enter)
        self.connect("key-press-event", self.on_key_press)
        self.connect("scroll-event", self.on_scroll)

        self.parent = parent
        self.trk = trk
        self.extras = trk.extras
        self.trkview = parent.trkview
        self.grid = Gtk.Grid()
        self.grid.set_column_spacing(3)
        self.grid.set_row_spacing(3)

        self.time_want_to_leave = 0

        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="edit-delete")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.connect("clicked", self.on_remove_button_clicked)
        button.set_tooltip_markup(
            cfg.tooltip_markup2 % ("delete", cfg.key["track_del"])
        )
        self.grid.attach(button, 2, 0, 1, 1)

        self.clone_button = Gtk.MenuButton()
        icon = Gio.ThemedIcon(name="edit-copy")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.clone_button.add(image)

        self.clone_button.set_tooltip_markup(
            cfg.tooltip_markup2 % ("clone", cfg.key["track_clone"])
        )

        self.clone_button.set_popup(Gtk.Menu())
        self.grid.attach(self.clone_button, 3, 0, 1, 1)

        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="list-remove")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.connect("clicked", self.on_retract_button_clicked)
        button.set_tooltip_markup(
            cfg.tooltip_markup2 % ("remove column", cfg.key["track_shrink"])
        )
        self.grid.attach(button, 0, 0, 1, 1)

        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="list-add")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.connect("clicked", self.on_expand_button_clicked)
        button.set_tooltip_markup(
            cfg.tooltip_markup2 % ("add column", cfg.key["track_expand"])
        )
        self.grid.attach(button, 1, 0, 1, 1)

        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="go-previous")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.connect("clicked", self.on_move_left_button_clicked)
        button.set_tooltip_markup(
            cfg.tooltip_markup2 % ("move left", cfg.key["track_move_left"])
        )
        self.grid.attach(button, 1, 1, 1, 1)

        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="go-next")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.connect("clicked", self.on_move_right_button_clicked)
        button.set_tooltip_markup(
            cfg.tooltip_markup2 % ("move right", cfg.key["track_move_right"])
        )
        self.grid.attach(button, 2, 1, 1, 1)

        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="go-first")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.connect("clicked", self.on_move_first_button_clicked)
        button.set_tooltip_markup(
            cfg.tooltip_markup2 % ("move to first", cfg.key["track_move_first"])
        )
        self.grid.attach(button, 0, 1, 1, 1)

        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="go-last")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.connect("clicked", self.on_move_last_button_clicked)
        button.set_tooltip_markup(
            cfg.tooltip_markup2 % ("move to last", cfg.key["track_move_last"])
        )
        self.grid.attach(button, 3, 1, 1, 1)

        self.extend_grid = Gtk.Grid()
        self.extend_grid.set_hexpand(True)
        self.extend_grid.set_vexpand(True)

        self.grid.attach(self.extend_grid, 4, 0, 5, 6)

        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(False)
        grid.set_column_spacing(3)
        grid.set_row_spacing(3)

        self.show_notes_button = Gtk.ToggleButton("notes")
        self.show_notes_button.set_tooltip_markup(
            cfg.tooltip_markup % (cfg.key["toggle_notes"])
        )
        self.show_timeshift_button = Gtk.ToggleButton("time")
        self.show_timeshift_button.set_tooltip_markup(
            cfg.tooltip_markup % (cfg.key["toggle_time"])
        )
        self.show_pitchwheel_button = Gtk.ToggleButton("pitch")
        self.show_pitchwheel_button.set_tooltip_markup(
            cfg.tooltip_markup % (cfg.key["toggle_pitch"])
        )
        self.show_controllers_button = Gtk.ToggleButton("ctrl")
        self.show_controllers_button.set_tooltip_markup(
            cfg.tooltip_markup % (cfg.key["toggle_controllers"])
        )
        self.show_probs_button = Gtk.ToggleButton("probs")
        self.show_probs_button.set_tooltip_markup(
            cfg.tooltip_markup % (cfg.key["toggle_probs"])
        )

        self.show_notes_button.set_vexpand(False)

        self.show_notes_button.connect("toggled", self.on_show_notes_toggled)
        self.show_timeshift_button.connect("toggled", self.on_show_timeshift_toggled)
        self.show_pitchwheel_button.connect("toggled", self.on_show_pitchwheel_toggled)
        self.show_controllers_button.connect(
            "toggled", self.on_show_controllers_toggled
        )
        self.show_probs_button.connect("toggled", self.on_show_probs_toggled)

        pad = Gtk.Label()
        pad.set_vexpand(True)
        grid.attach(pad, 0, 1, 1, 1)

        lab = Gtk.Label("show")
        lab.set_vexpand(True)

        grid.attach(lab, 0, 0, 1, 1)

        show_grid = Gtk.Grid()
        show_grid.set_column_homogeneous(True)
        show_grid.set_vexpand(True)
        show_grid.attach(self.show_notes_button, 0, 0, 1, 1)
        show_grid.attach(self.show_timeshift_button, 1, 0, 1, 1)
        show_grid.attach(self.show_pitchwheel_button, 2, 0, 1, 1)
        show_grid.attach(self.show_controllers_button, 3, 0, 1, 1)
        show_grid.attach(self.show_probs_button, 4, 0, 1, 1)
        grid.attach(show_grid, 1, 0, 4, 1)

        lab = Gtk.Label(cfg.quick_controls_desc)
        lab.set_vexpand(True)
        grid.attach(lab, 0, 2, 1, 1)
        lab.set_vexpand(True)

        self.quick_control_scale_1 = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 127, 1
        )
        self.quick_control_scale_2 = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 127, 1
        )

        qc = trk.get_qc()
        v1 = qc[1] if qc[1] > -1 else cfg.quick_control_1_def
        v2 = qc[3] if qc[3] > -1 else cfg.quick_control_2_def

        self.quick_control_scale_1.set_value(v1)
        self.quick_control_scale_2.set_value(v2)

        self.qc1_send_check_button = Gtk.CheckButton()
        self.qc1_send_check_button.connect("toggled", self.on_qc1_send_toggled)
        self.qc2_send_check_button = Gtk.CheckButton()
        self.qc2_send_check_button.connect("toggled", self.on_qc2_send_toggled)
        self.prog_send_check_button = Gtk.CheckButton()
        self.prog_send_check_button.connect("toggled", self.on_prog_send_toggled)

        # grid.attach(self.qc1_send_check_button, 1, 2, 1, 1)
        bx = Gtk.Box()
        bx.pack_start(self.qc1_send_check_button, False, False, 0)
        bx.pack_end(self.quick_control_scale_1, True, True, 0)
        grid.attach(bx, 1, 2, 2, 1)

        bx = Gtk.Box()
        bx.pack_start(self.qc2_send_check_button, False, False, 0)
        bx.pack_end(self.quick_control_scale_2, True, True, 0)
        grid.attach(bx, 3, 2, 2, 1)

        self.quick_control_scale_1.connect("value-changed", self.on_qc1_changed)
        self.quick_control_scale_2.connect("value-changed", self.on_qc2_changed)

        self.name_entry = Gtk.Entry()
        self.name_entry.connect("changed", self.on_name_changed)

        self.name_entry.set_activates_default(False)

        self.name_lab = Gtk.ToggleButton.new_with_label("name")
        self.name_lab.set_tooltip_markup(
            cfg.tooltip_markup % "hold name when switching patch"
        )
        self.name_lab.set_vexpand(True)

        self.name_lab.set_active(self.extras["track_keep_name"])

        self.name_lab.connect("toggled", self.on_keep_name_toggled)

        grid.attach(self.name_lab, 0, 4, 1, 1)
        grid.attach(self.name_entry, 1, 4, 4, 1)

        self.name_entry.set_text(self.extras["track_name"])

        self.show_timeshift_button.set_active(self.extras["track_show_timeshift"])

        self.show_pitchwheel_button.set_active(self.extras["track_show_pitchwheel"])
        self.show_controllers_button.set_active(self.extras["track_show_controllers"])
        self.show_notes_button.set_active(self.extras["track_show_notes"])

        lab = Gtk.Button.new_with_label("patch")
        lab.connect("button-press-event", self.on_resend_patch_clicked, 0)
        lab.set_tooltip_markup(
            cfg.tooltip_markup2 % ("resend patch", cfg.key["track_resend_patch"])
        )

        self.show_timeshift_button.set_active(self.extras["track_show_timeshift"])

        grid.attach(lab, 0, 3, 1, 1)

        box = Gtk.Box()

        self.patch_adj = Gtk.Adjustment(1, -1, 127, 1.0, 1.0)
        self.patch_button = Gtk.SpinButton()
        self.patch_button.set_adjustment(self.patch_adj)
        self.patch_adj.set_value(self.trk.get_program()[2])

        self.patch_adj.connect("value-changed", self.on_patch_value_changed)

        self.patch_menu = Gtk.Menu()

        i = 0
        for n, c in mod.bank.items():
            m = Gtk.MenuItem(n)
            sub = Gtk.Menu()
            subs = {}
            for p in c:
                if p[1] not in subs:
                    subs[p[1]] = []

                subs[p[1]].append((p[0], p[2]))

            for s in subs:
                if s:
                    mitm = Gtk.MenuItem(s)
                    mitmm = Gtk.Menu()
                    for p in subs[s]:
                        itm = Gtk.MenuItem(p[1])
                        itm.patch = p
                        itm.name = n
                        itm.connect("activate", self.on_patch_menu_item_activate)
                        itm.show()
                        mitmm.append(itm)
                    mitm.set_submenu(mitmm)
                    mitm.show()
                    sub.append(mitm)
                else:
                    for p in subs[s]:
                        mitm = Gtk.MenuItem(p[1])
                        mitm.patch = p
                        mitm.connect("activate", self.on_patch_menu_item_activate)
                        mitm.show()
                        sub.append(mitm)

            sub.show()
            m.set_submenu(sub)
            m.show()

            self.patch_menu.append(m)
            i += 1

        m = Gtk.SeparatorMenuItem()
        m.show()
        self.patch_menu.append(m)
        m = Gtk.MenuItem("clear")
        m.patch = -1
        m.connect("activate", self.on_patch_menu_item_activate)
        m.show()
        self.patch_menu.append(m)

        self.patch_menu_button = Gtk.MenuButton()
        self.patch_menu_button.set_popup(self.patch_menu)

        box.add(self.prog_send_check_button)
        box.add(self.patch_button)
        box.add(self.patch_menu_button)
        grid.attach(box, 1, 3, 2, 1)

        box = Gtk.Box()
        self.bank_msb = Gtk.Entry()
        lab = Gtk.Label("CC#0")
        self.bank_msb.set_text("%d" % self.trk.get_program()[0])
        self.bank_msb.set_input_purpose(Gtk.InputPurpose.DIGITS)
        self.bank_msb.set_width_chars(4)
        self.bank_msb.set_max_length(3)
        box.add(lab)
        box.add(self.bank_msb)
        grid.attach(box, 3, 3, 1, 1)

        box = Gtk.Box()
        self.bank_lsb = Gtk.Entry()
        lab = Gtk.Label("CC#32")
        self.bank_lsb.set_text("%d" % self.trk.get_program()[1])
        self.bank_lsb.set_input_purpose(Gtk.InputPurpose.DIGITS)
        self.bank_lsb.set_width_chars(4)
        self.bank_lsb.set_max_length(3)
        self.bank_lsb.set_hexpand(False)
        box.add(lab)
        box.add(self.bank_lsb)
        grid.attach(box, 4, 3, 1, 1)

        self.extend_track_grid = grid

        self.extend_controllers_grid = Gtk.Grid()

        grid = self.extend_controllers_grid

        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(True)
        grid.set_column_spacing(2)
        grid.set_row_spacing(2)

        self.extend_notebook = Gtk.Notebook()
        self.extend_notebook.set_hexpand(True)
        self.extend_notebook.set_vexpand(True)

        self.extend_notebook.connect("switch-page", self.on_notebook_page_switch)

        self.extend_notebook.append_page(
            self.extend_track_grid, NotebookLabel("track", self.extend_notebook, 0)
        )

        self.extend_grid.attach(self.extend_notebook, 0, 0, 3, 3)
        self.extend_grid.show()

        self.port_adj = Gtk.Adjustment(0, 0, 15, 1.0, 1.0)
        self.port_button = Gtk.SpinButton()
        self.port_button.set_adjustment(self.port_adj)
        self.port_adj.set_value(trk.port)
        self.port_adj.connect("value-changed", self.on_port_changed)

        lbl = Gtk.Label("port")
        lbl.set_xalign(1.0)

        self.grid.attach(lbl, 0, 2, 1, 1)
        self.grid.attach(self.port_button, 1, 2, 2, 1)

        self.channel_adj = Gtk.Adjustment(1, 1, 16, 1.0, 1.0)
        self.channel_button = Gtk.SpinButton()
        self.channel_button.set_adjustment(self.channel_adj)
        self.channel_adj.set_value(trk.channel)
        self.channel_adj.connect("value-changed", self.on_channel_changed)

        lbl = Gtk.Label("channel")
        lbl.set_xalign(1.0)

        self.grid.attach(lbl, 0, 3, 1, 1)
        self.grid.attach(self.channel_button, 1, 3, 2, 1)

        self.nsrows_adj = Gtk.Adjustment(1, 1, self.parent.seq.length, 1.0, 1.0)
        self.nsrows_button = Gtk.SpinButton()
        self.nsrows_button.set_adjustment(self.nsrows_adj)
        self.nsrows_adj.set_value(trk.nsrows)
        self.nsrows_adj.connect("value-changed", self.on_nsrows_changed)

        lbl = Gtk.Label("rows")
        lbl.set_xalign(1.0)

        self.nsrows_check_button = Gtk.CheckButton()
        self.nsrows_check_button.connect("toggled", self.on_nsrows_toggled)

        self.grid.attach(lbl, 0, 4, 1, 1)
        self.grid.attach(self.nsrows_button, 1, 4, 2, 1)
        self.grid.attach(self.nsrows_check_button, 3, 4, 1, 1)

        self.nrows_adj = Gtk.Adjustment(1, 1, 512, 1.0, 1.0)
        self.nrows_button = Gtk.SpinButton()
        self.nrows_button.set_adjustment(self.nrows_adj)
        self.nrows_adj.set_value(trk.nsrows)
        self.nrows_adj.connect("value-changed", self.on_nrows_changed)

        lbl = Gtk.Label("funk")
        lbl.set_xalign(1.0)

        self.nrows_check_button = Gtk.CheckButton()
        self.nrows_check_button.connect("toggled", self.on_nrows_toggled)

        self.grid.attach(lbl, 0, 5, 1, 1)
        self.grid.attach(self.nrows_button, 1, 5, 2, 1)
        self.grid.attach(self.nrows_check_button, 3, 5, 1, 1)

        self.nrows_button.set_sensitive(False)
        self.nsrows_button.set_sensitive(False)
        self.nrows_check_button.set_sensitive(False)

        self.ctrlsview = ControllersView(self.trk, self.trkview, self)
        self.extend_notebook.append_page(
            self.ctrlsview, NotebookLabel("controllers", self.extend_notebook, 1)
        )

        self.mandypage = Gtk.Box()

        self.mandymenu = MandyMenu(self.trk)
        self.mandyview = self.mandymenu.mandyview

        self.mandypage.pack_start(self.mandymenu, True, True, 0)

        self.extend_notebook.append_page(
            self.mandypage, NotebookLabel("mandy", self.extend_notebook, 2)
        )

        self.grid.show_all()
        self.add(self.grid)
        self.set_modal(False)

        self.extend_notebook.set_current_page(0)

    def on_resend_patch_clicked(self, wdg, evt, data):
        msb = -1
        lsb = -1
        c = int(self.patch_adj.get_value())

        if self.bank_msb.get_text().isnumeric():
            msb = int(self.bank_msb.get_text())

        if self.bank_lsb.get_text().isnumeric():
            lsb = int(self.bank_lsb.get_text())

        self.trk.set_bank(msb, lsb)
        self.trk.send_program_change(c)

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.hide()
            self.unpop()
            return True

        return False

    def on_scroll(self, wdg, prm):
        new = 0
        if prm.direction == Gdk.ScrollDirection.UP:
            new -= 1

        if prm.direction == Gdk.ScrollDirection.DOWN:
            new += 1

        new += self.trk.index

        if new > -1 and new < len(self.parent.seq):
            self.parent.propview.clear_popups()
            tv = self.parent.propview.trk_prop_cache[int(self.parent.seq[new])]
            tv.popover.pop()

        return False

    def build_clone_menu(self):
        m = self.clone_button.get_popup()
        for mm in m.get_children():
            mm.destroy()

        mitm = Gtk.MenuItem("here")
        mitm.seq = -1
        mitm.connect("activate", self.on_clone_menu_item_activate)
        mitm.show()
        m.append(mitm)

        mitm = Gtk.SeparatorMenuItem()
        mitm.show()
        m.append(mitm)

        for s in range(len(mod)):
            if s != mod.curr_seq:
                mitm = Gtk.MenuItem(mod[s].extras["sequence_name"])
                mitm.seq = int(s)
                mitm.connect("activate", self.on_clone_menu_item_activate)
                mitm.show()
                m.append(mitm)

        mitm = Gtk.SeparatorMenuItem()
        mitm.show()
        m.append(mitm)

        mitm = Gtk.MenuItem("new")
        mitm.seq = -23
        mitm.connect("activate", self.on_clone_menu_item_activate)
        mitm.show()
        m.append(mitm)

    def on_clone_menu_item_activate(self, itm):
        if itm.seq == -1:
            self.parent.clone_track(self.trkview)
            return

        seq = mod[itm.seq] if itm.seq != -23 else mod[mod.curr_seq]
        if itm.seq == -23:
            seq = mod.add_sequence(mod[mod.curr_seq].length)
            seq.rpb = mod[mod.curr_seq].rpb
            seq.extras["font_size"] = mod[self.parent.seq.index].extras["font_size"]
            trknm = self.trk.extras["track_name"]
            if trknm:
                seq.extras["sequence_name"] = trknm
            seq.ketchup()

        trk = self.parent.seq.clone_track(self.trkview.trk, seq)

        self.build_clone_menu()

    def on_patch_menu_item_activate(self, itm):
        if itm.patch == -1:
            self.trk.set_bank(-1, -1)
            self.trk.send_program_change(-1)
        else:
            self.trk.set_bank(*itm.patch[0][:2])
            self.trk.send_program_change(itm.patch[0][2])
            self.extras["last_patch_file"] = itm.name
            if not self.name_lab.get_active():
                self.name_entry.set_text(itm.patch[1])

        b = self.trk.get_program()
        self.patch_adj.set_value(b[2])
        self.bank_msb.set_text("%d" % b[0])
        self.bank_lsb.set_text("%d" % b[1])

    def refresh(self):
        if self.trkview.trk.nctrl == 1:
            self.show_controllers_button.set_sensitive(False)
            self.trkview.show_controllers = False
        else:
            self.show_controllers_button.set_sensitive(True)

        self.show_notes_button.set_active(self.trkview.show_notes)
        self.show_timeshift_button.set_active(self.trkview.show_timeshift)
        self.show_pitchwheel_button.set_active(self.trkview.show_pitchwheel)
        self.show_controllers_button.set_active(self.trkview.show_controllers)
        self.show_probs_button.set_active(self.trkview.show_probs)

        if not self.trkview.show_notes:
            self.show_controllers_button.set_sensitive(False)

        if not self.show_controllers_button.get_active():
            self.show_notes_button.set_sensitive(False)
        else:
            self.show_notes_button.set_sensitive(True)

        if self.trkview.trk.nrows != self.parent.seq.length:
            self.nsrows_button.set_sensitive(True)
            self.nsrows_check_button.set_active(True)

        if self.trkview.trk.nrows != self.trkview.trk.nsrows:
            self.nrows_button.set_sensitive(True)
            self.nrows_check_button.set_active(True)

        if self.trk.qc1_send:
            self.qc1_send_check_button.set_active(True)
            self.quick_control_scale_1.set_sensitive(True)
        else:
            self.qc1_send_check_button.set_active(False)
            self.quick_control_scale_1.set_sensitive(False)

        if self.trk.qc2_send:
            self.qc2_send_check_button.set_active(True)
            self.quick_control_scale_2.set_sensitive(True)
        else:
            self.qc2_send_check_button.set_active(False)
            self.quick_control_scale_2.set_sensitive(False)

        if self.trk.prog_send:
            self.prog_send_check_button.set_active(True)
            self.patch_button.set_sensitive(True)
            self.patch_menu_button.set_sensitive(True)
            self.bank_msb.set_sensitive(True)
            self.bank_lsb.set_sensitive(True)
        else:
            self.prog_send_check_button.set_active(False)
            self.patch_button.set_sensitive(False)
            self.patch_menu_button.set_sensitive(False)
            self.bank_msb.set_sensitive(False)
            self.bank_lsb.set_sensitive(False)

    def pop(self):
        mod.clear_popups(self)
        self.channel_adj.set_value(self.trk.channel)
        self.port_adj.set_value(self.trk.port)
        self.nsrows_adj.set_upper(self.parent.seq.length)
        self.nsrows_adj.set_value(self.trk.nsrows)
        self.nrows_adj.set_value(self.trk.nrows)
        self.port_adj.set_upper(mod.max_ports - 1)

        # self.loop_button.set_active(self.trk.loop) // not yet implemented in vhtlib
        # self.show_notes_button.set_sensitive(False)
        self.refresh()
        self.ctrlsview.rebuild()
        self.build_clone_menu()
        self.time_want_to_leave = 0
        self.add_tick_callback(self.tick)
        self.set_opacity(1)
        self.mandyview.entered = False
        self.trk.mandy.reset_anim()
        self.show()
        # self.popup()

    def tick(self, wdg, param):
        if self.parent.popped:
            if self.extend_notebook.get_current_page() == 2:
                self.mandyview.tick(wdg, param)
                self.time_want_to_leave = 0
                return True

        if self.time_want_to_leave == 0:  # normal
            op = self.get_opacity()
            if op < 1.0:
                self.set_opacity(op * 1.2)

            return True

        if self.time_want_to_leave == -1:  # closed - stop callback
            return False

        if self.ctrlsview.new_ctrl_menu.is_visible():
            self.time_want_to_leave = 0
            return True

        if self.patch_menu.is_visible():
            self.time_want_to_leave = 0
            return True

        if self.clone_button.get_popup().is_visible():
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
                self.unpop()

        return True

    def on_patch_value_changed(self, adj):
        c = int(adj.get_value())
        if c == -1:
            self.trk.set_bank(0, 0)
        else:
            self.trk.send_program_change(c)

        if self.name_lab.get_active():
            return

        curr = self.trk.get_program()
        self.name_entry.set_text("")
        # figure out the name
        if "last_patch_file" in self.extras:
            n = self.extras["last_patch_file"]
            if n in mod.bank:
                pf = mod.bank[n]
                for p in pf:
                    if p[0][2] == c and p[0][0] == curr[0] and p[0][1] == curr[1]:
                        self.name_entry.set_text(p[2])

    def on_leave(self, wdg, prm):
        if prm.window == self.get_window():
            if prm.detail != Gdk.NotifyType.INFERIOR:
                self.time_want_to_leave = datetime.now()
        return True

    def on_enter(self, wdg, prm):
        if prm.window == self.get_window():
            self.time_want_to_leave = 0
        return True

    def unpop(self):
        self.hide()
        self.time_want_to_leave = -1
        self.parent.button_highlight = False
        self.ctrlsview.capturing = False
        self.mandyview.entered = False
        self.parent.popped = False
        self.parent.redraw()

    def on_show_notes_toggled(self, wdg):
        self.extras["track_show_notes"] = wdg.get_active()
        if self.trkview.show_notes != wdg.get_active():
            self.trkview.toggle_notes()

        if wdg.get_active():
            self.show_controllers_button.set_sensitive(True)
        else:
            self.show_controllers_button.set_active(True)
            self.show_controllers_button.set_sensitive(False)

    def on_keep_name_toggled(self, wdg):
        self.extras["track_keep_name"] = wdg.get_active()

    def on_name_changed(self, wdg):
        self.extras["track_name"] = wdg.get_text()
        if self.parent.get_realized():
            self.parent.redraw()

    def on_show_timeshift_toggled(self, wdg):
        self.extras["track_show_timeshift"] = wdg.get_active()
        self.trkview.show_timeshift = wdg.get_active()
        if self.parent.popped:
            self.trkview.redraw_full()
            self.parent.redraw()

    def on_show_pitchwheel_toggled(self, wdg):
        self.extras["track_show_pitchwheel"] = wdg.get_active()
        if self.trkview.show_pitchwheel != wdg.get_active():
            self.trkview.toggle_pitch()

        if self.parent.popped:
            self.trkview.redraw_full()
            self.parent.redraw()

    def on_show_controllers_toggled(self, wdg):
        self.extras["track_show_controllers"] = wdg.get_active()
        if wdg.get_active():
            if self.trk.nctrl > 1:
                self.show_notes_button.set_sensitive(True)
        else:
            self.show_notes_button.set_active(True)
            self.show_notes_button.set_sensitive(False)

        if self.trkview.show_controllers != wdg.get_active():
            self.trkview.toggle_controls()

        if self.parent.popped:
            self.trkview.redraw_full()
            self.parent.redraw()

    def on_show_probs_toggled(self, wdg):
        self.extras["track_show_probs"] = wdg.get_active()
        if self.trkview.show_probs != wdg.get_active():
            self.trkview.toggle_probs()

        if self.parent.popped:
            self.trkview.redraw_full()
            self.parent.redraw()

    def on_remove_button_clicked(self, switch):
        if cfg.autosave_trk:
            mod.mainwin.app.autosave()
        self.parent.del_track()

    def on_retract_button_clicked(self, switch):
        self.parent.seqview.shrink_track(self.trk)

    def on_expand_button_clicked(self, switch):
        self.parent.seqview.expand_track(self.trk)

    def on_port_changed(self, adj):
        self.trk.port = int(adj.get_value())
        mod.midi_synch_ports()
        self.parent.redraw()

    def on_channel_changed(self, adj):
        self.trk.channel = int(adj.get_value())
        self.parent.redraw()

    def on_nrows_changed(self, adj):
        self.trk.nrows = int(adj.get_value())
        if self.trkview.edit and self.trkview.edit[1] >= self.trk.nrows:
            self.trkview.leave_all()

        self.trkview.select_end, self.trkview.select_start = None, None
        self.parent.seqview.recalculate_row_spacing()

    def on_nsrows_changed(self, adj):
        self.trk.nsrows = int(adj.get_value())

        if not self.nrows_check_button.get_active():
            self.trk.nrows = int(adj.get_value())
            self.nrows_adj.set_value(adj.get_value())

        self.trkview.select_end, self.trkview.select_start = None, None
        self.parent.seqview.recalculate_row_spacing()

    def on_prog_send_toggled(self, wdg):
        self.trk.prog_send = wdg.get_active()
        self.refresh()

    def on_qc1_send_toggled(self, wdg):
        self.trk.qc1_send = wdg.get_active()
        self.refresh()

    def on_qc2_send_toggled(self, wdg):
        self.trk.qc2_send = wdg.get_active()
        self.refresh()

    def on_nrows_toggled(self, wdg):
        if wdg.get_active():
            self.nrows_button.set_sensitive(True)
            self.nsrows_check_button.set_sensitive(True)
        else:
            self.nrows_button.set_sensitive(False)
            self.nrows_adj.set_value(self.nsrows_adj.get_value())
            self.nrows_check_button.set_active(False)

    def on_nsrows_toggled(self, wdg):
        if wdg.get_active():
            self.nsrows_button.set_sensitive(True)
            self.nrows_check_button.set_sensitive(True)
        else:
            self.nrows_adj.set_value(self.parent.seq.length)
            self.nsrows_adj.set_value(self.parent.seq.length)
            self.nsrows_button.set_sensitive(False)
            self.nrows_button.set_sensitive(False)
            self.nrows_check_button.set_active(False)
            self.nrows_check_button.set_sensitive(False)

    def on_move_left_button_clicked(self, switch):
        self.parent.move_left()

    def on_move_right_button_clicked(self, switch):
        self.parent.move_right()

    def on_move_first_button_clicked(self, switch):
        self.parent.move_first()

    def on_move_last_button_clicked(self, switch):
        self.parent.move_last()

    def on_qc1_changed(self, adj):
        qc = self.trk.get_qc()
        self.trk.set_qc1(
            qc[0] if qc[0] > -1 else cfg.quick_control_1_ctrl, int(adj.get_value())
        )

    def on_qc2_changed(self, adj):
        qc = self.trk.get_qc()
        self.trk.set_qc2(
            qc[2] if qc[2] > -1 else cfg.quick_control_2_ctrl, int(adj.get_value())
        )

    def on_notebook_page_switch(self, wdg, opg, pg):
        if pg == 2:
            self.trk.mandy.reset_anim()
