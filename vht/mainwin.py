# mainwin.py - Valhalla Tracker
#
# Copyright (C) 2020 Remigiusz Dybka - remigiusz.dybka@gmail.com
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

from vht.console import Console
from vht.sequencelistview import SequenceListView
from vht.statusbar import StatusBar
from vht.sequenceview import SequenceView
from vht import *
import vht.extras

import gi
import os

gi.require_version("Gtk", "3.0")
gi.require_version("Vte", "2.91")
from gi.repository import Gtk, Gdk, Gio


class MainWin(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)

        self.fs = False
        self.app = app
        mod.mainwin = self
        self.timeline_visible = False
        mod.console_visible = False
        self.last_filename = None
        self.last_filename_naked = None

        # here we GUI
        st = self.get_settings()
        st.set_property("gtk-application-prefer-dark-theme", cfg.dark_theme)

        self.set_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.connect("key-press-event", self.on_key_press)

        self.hb = Gtk.HeaderBar()
        self.hb.set_show_close_button(True)
        # self.hb.set_has_subtitle(False)
        self.set_titlebar(self.hb)
        self.set_default_icon_name("vht")
        self.set_icon_name("vht")
        self.set_icon_from_file(os.path.join(mod.data_path, "vht.svg"))

        self.set_opacity(cfg.window_opacity)
        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="media-playback-stop")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.connect("clicked", self.on_stop_button_activate)
        self.hb.pack_start(button)

        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="media-playback-start")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.connect("clicked", self.on_start_button_activate)
        self.hb.pack_start(button)

        label = Gtk.Label("BPM:")
        self.hb.pack_start(label)

        self.adj = Gtk.Adjustment(120.0, mod.min_bpm, mod.max_bpm, 1, 10.0, 1.0)
        self.bpmbutton = Gtk.SpinButton()
        self.bpmbutton.set_adjustment(self.adj)
        self.bpmbutton.set_digits(2)
        # self.bpmbutton.set_snap_to_ticks(True)
        self.bpmbutton.set_numeric(True)
        self.bpmbutton.set_increments(1, 10)

        self.hb.pack_start(self.bpmbutton)
        self.adj.set_value(mod.bpm)
        self.adj.connect("value-changed", self.on_bpm_changed)

        self.time_display = Gtk.Label()
        self.time_display.use_markup = True

        self.hb.pack_end(Gtk.Separator())
        self.menubutt = Gtk.MenuButton()
        icon = Gio.ThemedIcon(name="open-menu-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.menubutt.add(image)
        self.menubutt.set_use_popover(True)

        with open(os.path.join(mod.data_path, "menu.ui"), "r") as f:
            builder = Gtk.Builder.new_from_string(f.read(), -1)
            menu = builder.get_object("app-menu")
            self.menubutt.set_menu_model(menu)

        self.hb.pack_end(self.menubutt)
        self.hb.pack_end(self.time_display)

        self.vbox = Gtk.Box()
        self.hbox = Gtk.Paned()
        self.seqbox = Gtk.Paned()
        self.seqbox.set_orientation(Gtk.Orientation.VERTICAL)

        self._sequence_view = SequenceView(mod[0])
        self.hbox.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.seqbox.pack1(self._sequence_view, True, True)

        self.hbox.pack1(self.seqbox, True, True)
        self.console = Console()

        self.timeline_box = Gtk.Paned()
        self.timeline_box.set_orientation(Gtk.Orientation.VERTICAL)
        self.timeline_box.set_wide_handle(True)

        self.seqlist = SequenceListView()
        mod.seqlist = self.seqlist
        self.seq_add_butt = Gtk.Button()
        self.seq_mode_butt = Gtk.ToggleButton()
        self.seq_mode_butt.set_active(True)
        self.butt_panic = Gtk.Button()

        icon = Gio.ThemedIcon(name="list-add")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.seq_add_butt.add(image)
        self.seq_add_butt.connect("clicked", self.on_seq_add_butt_clicked)
        self.seq_add_butt.set_tooltip_markup(
            cfg.tooltip_markup % (cfg.key["sequence_add"])
        )

        icon = Gio.ThemedIcon(name="process-stop")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.butt_panic.add(image)
        self.butt_panic.connect("clicked", self.on_butt_panic_clicked)
        self.butt_panic.set_tooltip_markup(cfg.tooltip_markup % (cfg.key["panic"]))

        icon = Gio.ThemedIcon(name="media-playlist-repeat")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.seq_mode_butt.add(image)
        # self.seq_mode_butt.connect("clicked", self.on_butt_panic_clicked)
        # self.seq_mode_butt.set_tooltip_markup(cfg.tooltip_markup % (cfg.key["panic"]))

        buttbox = Gtk.Box()
        buttbox.set_orientation(Gtk.Orientation.VERTICAL)
        buttbox.pack_end(self.seq_mode_butt, False, True, 0)
        buttbox.pack_end(self.butt_panic, False, True, 0)
        buttbox.pack_end(self.seq_add_butt, False, True, 0)

        seqpane = Gtk.Paned()
        seqpane.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.seqlist_sw = Gtk.ScrolledWindow()
        self.seqlist_sw.add_with_viewport(self.seqlist)

        seqpane.pack1(self.seqlist_sw, True, True)
        seqpane.pack2(buttbox, False, False)

        self.timeline_box.pack1(seqpane, False, False)
        self.timeline_box.pack2(Gtk.Label("timeliner"), True, True)
        self.timeline_box.set_position(cfg.timeline_position_y)

        self.vbox.pack_start(self.hbox, True, True, 0)
        self._status_bar = StatusBar()
        self.vbox.pack_end(self._status_bar, False, True, 0)
        self.vbox.set_orientation(Gtk.Orientation.VERTICAL)

        self.add(self.vbox)

        self.set_default_size(800, 600)
        self.show_all()

        self._sequence_view._sv.grab_focus()

        if cfg.console_show:
            self.show_console()

        if cfg.timeline_show:
            self.show_timeline()

        if mod.start_error:
            dialog = Gtk.MessageDialog(
                self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, mod.start_error
            )

            dialog.run()
            dialog.destroy()

        self.add_tick_callback(self.tick)

    def tick(self, wdg, param):
        self.time_display.set_markup(
            """<span font_desc="Roboto bold" font_family="monospace" size="x-large">%s</span>"""
            % mod.time
        )
        return 1

    def on_start_button_activate(self, switch):
        mod.play = 1

    def on_stop_button_activate(self, switch):
        if not mod.play:
            mod.reset()
        else:
            pass

        mod.play = False

    def on_seq_add_butt_clicked(self, butt):
        self._sequence_view.seq_add()

    def on_butt_panic_clicked(self, butt):
        mod.panic()

    def on_bpm_changed(self, adj):
        mod.bpm = adj.get_value()

    def hide_timeline(self):
        if not self.timeline_visible:
            return

        self.timeline_box.hide()

        self.timeline_visible = False

    def show_timeline(self):
        if self.timeline_visible:
            return

        if 1 == len(self.hbox.get_children()):
            self.hbox.pack2(self.timeline_box, False, True)
            self.hbox.set_position(
                self.get_window().get_width() * cfg.timeline_position
            )

        self.hbox.set_wide_handle(True)
        self.timeline_visible = True
        self.timeline_box.show_all()

    def hide_console(self):
        if not mod.console_visible:
            return

        self.console.hide()
        mod.console_visible = False
        self._sequence_view.auto_scroll_req = True

    def show_console(self):
        if mod.console_visible:
            return

        if 1 == len(self.seqbox.get_children()):
            self.seqbox.pack2(self.console, True, True)
            self.seqbox.set_position(
                self.get_window().get_height() * cfg.console_position
            )

        mod.console_visible = True
        self.seqbox.set_wide_handle(True)
        self._sequence_view.auto_scroll_req = True
        self.seqbox.show_all()

    def on_key_press(self, wdg, event):
        if cfg.key["toggle_timeline"].matches(event):
            if self.timeline_visible:
                self.hide_timeline()
                self.hbox.set_wide_handle(False)
            else:
                self.show_timeline()
            return True

        if cfg.key["toggle_console"].matches(event):
            if mod.console_visible:
                self.hide_console()
                self.seqbox.set_wide_handle(False)
            else:
                self.show_console()

        return False

    def set_header_from_filename(self, filename):
        if not filename:
            self.hb.set_title(None)
            self.hb.set_subtitle(None)
            return

        title = os.path.split(filename)[1]
        if title.endswith(".vht"):
            title = title[:-4]

        self.hb.set_title(title)
        self.hb.set_subtitle(
            os.path.split(os.path.normpath(filename))[0].replace("//", "/")
        )

    def load(self, filename):
        self.set_header_from_filename(None)

        if not self._sequence_view.load(filename):
            return False

        self.last_filename = filename
        self.set_header_from_filename(filename)
        self.adj.set_value(mod.bpm)
        return True
