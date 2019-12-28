# trackpropviewpopover.py - Valhalla Tracker
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
from vht.controllersview import ControllersView
from vht import cfg, mod
from gi.repository import Gdk, Gtk, Gio
from datetime import datetime
import gi

gi.require_version("Gtk", "3.0")


class TrackPropViewPopover(Gtk.Popover):
    def __init__(self, parent, trk):
        super(TrackPropViewPopover, self).__init__()
        self.set_relative_to(parent)

        self.add_events(
            Gdk.EventMask.LEAVE_NOTIFY_MASK | Gdk.EventMask.ENTER_NOTIFY_MASK
        )

        self.connect("leave-notify-event", self.on_leave)
        self.connect("enter-notify-event", self.on_enter)

        self.parent = parent
        self.trk = trk
        self.trkview = parent.trkview
        self.grid = Gtk.Grid()
        self.grid.set_column_spacing(3)
        self.grid.set_row_spacing(3)

        self.time_want_to_leave = 0

        if trk:
            button = Gtk.Button()
            icon = Gio.ThemedIcon(name="edit-delete")
            image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
            button.add(image)
            button.connect("clicked", self.on_remove_button_clicked)
            button.set_tooltip_markup(cfg.tooltip_markup % (cfg.key["track_del"]))
            self.grid.attach(button, 2, 0, 1, 1)

            self.clone_button = Gtk.MenuButton()
            icon = Gio.ThemedIcon(name="edit-copy")
            image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
            self.clone_button.add(image)

            self.clone_button.set_tooltip_markup(
                cfg.tooltip_markup % (cfg.key["track_clone"])
            )

            self.clone_button.set_popup(Gtk.Menu())
            self.grid.attach(self.clone_button, 3, 0, 1, 1)

            button = Gtk.Button()
            icon = Gio.ThemedIcon(name="list-remove")
            image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
            button.add(image)
            button.connect("clicked", self.on_retract_button_clicked)
            button.set_tooltip_markup(cfg.tooltip_markup % (cfg.key["track_shrink"]))
            self.grid.attach(button, 0, 0, 1, 1)

            button = Gtk.Button()
            icon = Gio.ThemedIcon(name="list-add")
            image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
            button.add(image)
            button.connect("clicked", self.on_expand_button_clicked)
            button.set_tooltip_markup(cfg.tooltip_markup % (cfg.key["track_expand"]))
            self.grid.attach(button, 1, 0, 1, 1)

            button = Gtk.Button()
            icon = Gio.ThemedIcon(name="go-previous")
            image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
            button.add(image)
            button.connect("clicked", self.on_move_left_button_clicked)
            button.set_tooltip_markup(cfg.tooltip_markup % (cfg.key["track_move_left"]))
            self.grid.attach(button, 1, 1, 1, 1)

            button = Gtk.Button()
            icon = Gio.ThemedIcon(name="go-next")
            image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
            button.add(image)
            button.connect("clicked", self.on_move_right_button_clicked)
            button.set_tooltip_markup(
                cfg.tooltip_markup % (cfg.key["track_move_right"])
            )
            self.grid.attach(button, 2, 1, 1, 1)

            button = Gtk.Button()
            icon = Gio.ThemedIcon(name="go-first")
            image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
            button.add(image)
            button.connect("clicked", self.on_move_first_button_clicked)
            button.set_tooltip_markup(
                cfg.tooltip_markup % (cfg.key["track_move_first"])
            )
            self.grid.attach(button, 0, 1, 1, 1)

            button = Gtk.Button()
            icon = Gio.ThemedIcon(name="go-last")
            image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
            button.add(image)
            button.connect("clicked", self.on_move_last_button_clicked)
            button.set_tooltip_markup(cfg.tooltip_markup % (cfg.key["track_move_last"]))
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
                cfg.tooltip_markup % (cfg.key["toggle_controls"])
            )

            self.show_notes_button.connect("toggled", self.on_show_notes_toggled)
            self.show_timeshift_button.connect(
                "toggled", self.on_show_timeshift_toggled
            )
            self.show_pitchwheel_button.connect(
                "toggled", self.on_show_pitchwheel_toggled
            )
            self.show_controllers_button.connect(
                "toggled", self.on_show_controllers_toggled
            )

            lab = Gtk.Label("show:")
            lab.set_vexpand(True)
            grid.attach(lab, 0, 0, 1, 1)
            grid.attach(self.show_notes_button, 1, 0, 1, 1)
            grid.attach(self.show_timeshift_button, 2, 0, 1, 1)
            grid.attach(self.show_pitchwheel_button, 3, 0, 1, 1)
            grid.attach(self.show_controllers_button, 4, 0, 1, 1)

            grid.attach(Gtk.Label(cfg.quick_controls_desc), 0, 1, 1, 1)

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

            grid.attach(self.quick_control_scale_1, 1, 1, 2, 1)
            grid.attach(self.quick_control_scale_2, 3, 1, 2, 1)

            self.quick_control_scale_1.connect("value-changed", self.on_qc1_changed)
            self.quick_control_scale_2.connect("value-changed", self.on_qc2_changed)

            self.name_entry = Gtk.Entry()
            self.name_entry.connect("changed", self.on_name_changed)

            self.name_entry.set_activates_default(False)

            grid.attach(Gtk.Label("name:"), 0, 3, 1, 1)
            grid.attach(self.name_entry, 1, 3, 4, 1)

            if not parent.seq.index in mod.extras:
                mod.extras[parent.seq.index] = {}

            if not self.trk.index in mod.extras[parent.seq.index]:
                mod.extras[parent.seq.index][self.trk.index] = {}

            if not "track_name" in mod.extras[parent.seq.index][self.trk.index]:
                mod.extras[parent.seq.index][self.trk.index]["track_name"] = ""

            self.name_entry.set_text(
                mod.extras[parent.seq.index][self.trk.index]["track_name"]
            )

            if "track_show_notes" in mod.extras[self.parent.seq.index][self.trk.index]:
                self.show_timeshift_button.set_active(
                    mod.extras[self.parent.seq.index][self.trk.index][
                        "track_show_timeshift"
                    ]
                )
                self.show_pitchwheel_button.set_active(
                    mod.extras[self.parent.seq.index][self.trk.index][
                        "track_show_pitchwheel"
                    ]
                )
                self.show_controllers_button.set_active(
                    mod.extras[self.parent.seq.index][self.trk.index][
                        "track_show_controllers"
                    ]
                )
                self.show_notes_button.set_active(
                    mod.extras[self.parent.seq.index][self.trk.index][
                        "track_show_notes"
                    ]
                )
            else:
                mod.extras[self.parent.seq.index][self.trk.index][
                    "track_show_notes"
                ] = True
                mod.extras[self.parent.seq.index][self.trk.index][
                    "track_show_timeshift"
                ] = False
                mod.extras[self.parent.seq.index][self.trk.index][
                    "track_show_pitchwheel"
                ] = False
                mod.extras[self.parent.seq.index][self.trk.index][
                    "track_show_controllers"
                ] = False

            grid.attach(Gtk.Label("patch:"), 0, 2, 1, 1)

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

            self.patch_menu_button = Gtk.MenuButton()
            self.patch_menu_button.set_popup(self.patch_menu)

            box.add(self.patch_button)
            box.add(self.patch_menu_button)

            grid.attach(box, 1, 2, 2, 1)

            self.extend_track_grid = grid

            self.extend_controllers_grid = Gtk.Grid()

            grid = self.extend_controllers_grid

            grid.set_column_homogeneous(True)
            grid.set_row_homogeneous(True)
            grid.set_column_spacing(2)
            grid.set_row_spacing(2)

            self.ctrlsview = ControllersView(self.trk, self.trkview, self)

            self.extend_notebook = Gtk.Notebook()
            self.extend_notebook.set_hexpand(True)
            self.extend_notebook.set_vexpand(True)

            self.extend_notebook.append_page(
                self.extend_track_grid, NotebookLabel("track", self.extend_notebook, 0)
            )
            self.extend_notebook.append_page(
                self.ctrlsview, NotebookLabel("controllers", self.extend_notebook, 1)
            )

            self.extend_grid.attach(self.extend_notebook, 0, 0, 3, 3)
            self.extend_grid.show()

            self.port_adj = Gtk.Adjustment(0, 0, 15, 1.0, 1.0)
            self.port_button = Gtk.SpinButton()
            self.port_button.set_adjustment(self.port_adj)
            self.port_adj.set_value(trk.port)
            self.port_adj.connect("value-changed", self.on_port_changed)

            lbl = Gtk.Label("port:")
            lbl.set_xalign(1.0)

            self.grid.attach(lbl, 0, 2, 1, 1)
            self.grid.attach(self.port_button, 1, 2, 2, 1)

            self.channel_adj = Gtk.Adjustment(1, 1, 16, 1.0, 1.0)
            self.channel_button = Gtk.SpinButton()
            self.channel_button.set_adjustment(self.channel_adj)
            self.channel_adj.set_value(trk.channel)
            self.channel_adj.connect("value-changed", self.on_channel_changed)

            lbl = Gtk.Label("channel:")
            lbl.set_xalign(1.0)

            self.grid.attach(lbl, 0, 3, 1, 1)
            self.grid.attach(self.channel_button, 1, 3, 2, 1)

            self.nsrows_adj = Gtk.Adjustment(1, 1, self.parent.seq.length, 1.0, 1.0)
            self.nsrows_button = Gtk.SpinButton()
            self.nsrows_button.set_adjustment(self.nsrows_adj)
            self.nsrows_adj.set_value(trk.nsrows)
            self.nsrows_adj.connect("value-changed", self.on_nsrows_changed)

            lbl = Gtk.Label("rows:")
            lbl.set_xalign(1.0)

            self.nsrows_check_button = Gtk.CheckButton()
            self.nsrows_check_button.connect("toggled", self.on_nsrows_toggled)

            self.grid.attach(lbl, 0, 4, 1, 1)
            self.grid.attach(self.nsrows_button, 1, 4, 2, 1)
            self.grid.attach(self.nsrows_check_button, 3, 4, 1, 1)

            self.nrows_adj = Gtk.Adjustment(1, 1, 256, 1.0, 1.0)
            self.nrows_button = Gtk.SpinButton()
            self.nrows_button.set_adjustment(self.nrows_adj)
            self.nrows_adj.set_value(trk.nsrows)
            self.nrows_adj.connect("value-changed", self.on_nrows_changed)

            lbl = Gtk.Label("funk:")
            lbl.set_xalign(1.0)

            self.nrows_check_button = Gtk.CheckButton()
            self.nrows_check_button.connect("toggled", self.on_nrows_toggled)

            self.grid.attach(lbl, 0, 5, 1, 1)
            self.grid.attach(self.nrows_button, 1, 5, 2, 1)
            self.grid.attach(self.nrows_check_button, 3, 5, 1, 1)

            self.nrows_button.set_sensitive(False)
            self.nsrows_button.set_sensitive(False)
            self.nrows_check_button.set_sensitive(False)

            self.grid.show_all()
            self.add(self.grid)

            self.extend_notebook.set_current_page(0)
            self.set_modal(False)

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
                mitm = Gtk.MenuItem(mod.extras[s][-1]["sequence_name"])
                mitm.seq = int(s)
                mitm.connect("activate", self.on_clone_menu_item_activate)
                mitm.show()
                m.append(mitm)

    def on_clone_menu_item_activate(self, itm):
        if itm.seq == -1:
            self.parent.clone_track(self.trkview)
            return

        ntrk = self.parent.seq.clone_track(self.trkview.trk, mod[itm.seq])
        mod.extras[itm.seq][ntrk.index] = mod.extras[self.parent.seq.index][
            self.trk.index
        ].copy()

    def on_patch_menu_item_activate(self, itm):
        self.name_entry.set_text(itm.patch[1])
        self.trk.set_bank(*itm.patch[0][:2])
        self.patch_adj.set_value(itm.patch[0][2])
        mod.extras[self.parent.seq.index][self.trk.index]["last_patch_file"] = itm.name

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

        if not self.trkview.show_notes:
            self.show_controllers_button.set_sensitive(False)

        if not self.show_controllers_button.get_active():
            self.show_notes_button.set_sensitive(False)
        else:
            self.show_notes_button.set_sensitive(True)

    def pop(self):
        mod.clear_popups(self)
        self.channel_adj.set_value(self.trk.channel)
        self.port_adj.set_value(self.trk.port)
        self.nsrows_adj.set_upper(self.parent.seq.length)
        self.nsrows_adj.set_value(self.trk.nsrows)
        self.nrows_adj.set_value(self.trk.nrows)
        self.port_adj.set_upper(mod.nports - 1)

        # self.loop_button.set_active(self.trk.loop) // not yet implemented in vhtlib
        # self.show_notes_button.set_sensitive(False)
        self.refresh()
        self.ctrlsview.rebuild()
        self.build_clone_menu()
        self.time_want_to_leave = 0
        self.add_tick_callback(self.tick)
        self.set_opacity(1)
        self.show()
        # self.popup()

    def tick(self, wdg, param):
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
        self.trk.send_program_change(c)

        # figure out the name
        if "last_patch_file" in mod.extras[self.parent.seq.index][self.trk.index]:
            n = mod.extras[self.parent.seq.index][self.trk.index]["last_patch_file"]
            if n in mod.bank:
                pf = mod.bank[n]
                for p in pf:
                    if p[0][2] == c:
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
        self.popdown()
        self.time_want_to_leave = -1
        self.parent.button_highlight = False
        self.ctrlsview.capturing = False
        self.parent.popped = False
        self.parent.redraw()

    def on_show_notes_toggled(self, wdg):
        mod.extras[self.parent.seq.index][self.trk.index][
            "track_show_notes"
        ] = wdg.get_active()
        if self.trkview.show_notes != wdg.get_active():
            self.trkview.toggle_notes()

        if wdg.get_active():
            self.show_controllers_button.set_sensitive(True)
        else:
            self.show_controllers_button.set_active(True)
            self.show_controllers_button.set_sensitive(False)

    def on_name_changed(self, wdg):
        mod.extras[self.parent.seq.index][self.trk.index]["track_name"] = wdg.get_text()
        if self.parent.get_realized():
            self.parent.redraw()

    def on_show_timeshift_toggled(self, wdg):
        mod.extras[self.parent.seq.index][self.trk.index][
            "track_show_timeshift"
        ] = wdg.get_active()
        self.trkview.show_timeshift = wdg.get_active()
        if self.parent.popped:
            self.trkview.redraw_full()
            self.parent.redraw()

    def on_show_pitchwheel_toggled(self, wdg):
        mod.extras[self.parent.seq.index][self.trk.index][
            "track_show_pitchwheel"
        ] = wdg.get_active()
        if self.trkview.show_pitchwheel != wdg.get_active():
            self.trkview.toggle_pitch()

        if self.parent.popped:
            self.trkview.redraw_full()
            self.parent.redraw()

    def on_show_controllers_toggled(self, wdg):
        mod.extras[self.parent.seq.index][self.trk.index][
            "track_show_controllers"
        ] = wdg.get_active()
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

    def on_remove_button_clicked(self, switch):
        self.parent.del_track()

    def on_retract_button_clicked(self, switch):
        self.parent.seqview.shrink_track(self.trk)

    def on_expand_button_clicked(self, switch):
        self.parent.seqview.expand_track(self.trk)

    def on_port_changed(self, adj):
        self.trk.port = int(adj.get_value())
        self.parent.redraw()

    def on_channel_changed(self, adj):
        self.trk.channel = int(adj.get_value())
        self.parent.redraw()

    def on_nrows_changed(self, adj):
        self.trk.nrows = int(adj.get_value())
        self.parent.seqview.recalculate_row_spacing()

    def on_nsrows_changed(self, adj):
        self.trk.nsrows = int(adj.get_value())

        if not self.nrows_check_button.get_active():
            self.trk.nrows = int(adj.get_value())
            self.nrows_adj.set_value(adj.get_value())

        self.parent.seqview.recalculate_row_spacing()

    def on_nrows_toggled(self, wdg):
        if wdg.get_active():
            self.nrows_button.set_sensitive(True)
            self.nsrows_check_button.set_sensitive(True)
        else:
            self.nrows_button.set_sensitive(False)
            self.nrows_check_button.set_active(False)
            self.nrows_adj.set_value(self.nsrows_adj.get_value())

    def on_nsrows_toggled(self, wdg):
        if wdg.get_active():
            self.nsrows_button.set_sensitive(True)
            self.nrows_check_button.set_sensitive(True)
        else:
            self.nsrows_button.set_sensitive(False)
            self.nrows_button.set_sensitive(False)
            self.nrows_check_button.set_active(False)
            self.nrows_check_button.set_sensitive(False)

            self.nrows_adj.set_value(self.parent.seq.length)
            self.nsrows_adj.set_value(self.parent.seq.length)

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
