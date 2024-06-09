# mainwin.py - vahatraker
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

from vht.sequencelistview import SequenceListView
from vht.timelineview import TimelineView
from vht.statusbar import StatusBar
from vht.sequenceview import SequenceView
from vht.thumbmanager import ThumbManager
from vht.renderer import Renderer
from vht.portconfig import *

from vht.portconfigpopover import PortConfigPopover

from vht import *
import vht.extras

import gi
import os

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, Gdk, Gio

try:
    gi.require_version("Vte", "2.91")
    from vht.console import Console
except Exception:
    Console = None


class MainWin(Gtk.ApplicationWindow):
    def __init__(self, app):
        super(MainWin, self).__init__(application=app)
        # here we GUI

        self.fs = False
        self.app = app
        mod.mainwin = self
        mod.thumbmanager = ThumbManager(mod)
        self.timeline_visible = False
        mod.console_visible = False
        mod.renderer = Renderer(mod, cfg)
        self.last_filename = None
        self.last_filename_naked = None

        # self.set_interactive_debugging(True)
        st = self.get_settings()
        st.set_property("gtk-application-prefer-dark-theme", cfg.dark_theme)

        self.set_events(Gdk.EventMask.KEY_PRESS_MASK | Gdk.EventMask.KEY_RELEASE_MASK)
        self.connect("key-press-event", self.on_key_press)
        self.connect("key-release-event", self.on_key_release)
        self.connect("delete-event", self.on_destroy)

        if "timeline_win_pos_y" in mod.extras:
            cfg.timeline_position_y = mod.extras["timeline_win_pos_y"]

        if "timeline_win_pos" in mod.extras:
            cfg.timeline_position = mod.extras["timeline_win_pos"]

        self.hb = Gtk.HeaderBar()
        self.hb.set_show_close_button(True)
        # self.hb.set_has_subtitle(False)
        self.set_titlebar(self.hb)
        self.set_default_icon_name("io.github.rdybka.vht")
        self.set_icon_name("io.github.rdybka.vht")
        self.set_icon_from_file(os.path.join(mod.data_path, "vht.svg"))

        self.set_opacity(cfg.window_opacity)
        button_start = Gtk.Button()
        icon = Gio.ThemedIcon(name="media-playback-stop")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button_start.add(image)
        button_start.connect("clicked", self.on_stop_button_activate)
        button_start.set_tooltip_markup(
            cfg.tooltip_markup
            % ("stop %s\nreset %s" % (cfg.key["play"], cfg.key["reset"]))
        )

        button_stop = Gtk.Button()
        icon = Gio.ThemedIcon(name="media-playback-start")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button_stop.add(image)
        button_stop.connect("clicked", self.on_start_button_activate)
        button_stop.set_tooltip_markup(cfg.tooltip_markup2 % ("play", cfg.key["play"]))

        self.transport_switch = Gtk.Switch()
        self.transport_switch.set_state(cfg.start_transport)
        self.transport_switch.set_tooltip_markup(
            cfg.tooltip_markup2 % ("transport", cfg.key["toggle_transport"])
        )
        self.transport_switch.connect("state-set", self.on_transport_switch)

        self.time_display = Gtk.Label()
        self.time_display.use_markup = True

        # self.hb.pack_end(Gtk.Separator())
        self.menubutt = Gtk.MenuButton()
        icon = Gio.ThemedIcon(name="open-menu-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.menubutt.add(image)
        self.menubutt.set_use_popover(True)

        menu_phile = "menu.ui" if Console else "menu_norend.ui"

        with open(os.path.join(mod.data_path, menu_phile), "r") as f:
            builder = Gtk.Builder.new_from_string(f.read(), -1)
            menu = builder.get_object("app-menu")
            self.menubutt.set_menu_model(menu)

        self.hb.pack_start(button_start)
        self.hb.pack_start(button_stop)
        self.hb.pack_start(self.transport_switch)
        self.hb.pack_end(self.menubutt)
        self.hb.pack_end(self.time_display)

        self.vbox = Gtk.Box()
        self.hbox = Gtk.Paned()
        self.seqbox = Gtk.Paned()
        self.seqbox.set_orientation(Gtk.Orientation.VERTICAL)

        self.sequence_view = SequenceView(mod[mod.curr_seq])
        self.hbox.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.seqbox.pack1(self.sequence_view, True, True)

        self.hbox.pack1(self.seqbox, True, True)
        if Console:
            self.console = Console()
        else:
            self.console = None

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
            cfg.tooltip_markup2 % ("add seq", cfg.key["sequence_add"])
        )

        icon = Gio.ThemedIcon(name="process-stop")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.butt_panic.add(image)
        self.butt_panic.connect("pressed", self.on_butt_panic_pressed)
        self.butt_panic.connect("released", self.on_butt_panic_released)
        self.butt_panic.set_tooltip_markup(
            cfg.tooltip_markup2 % ("panique", cfg.key["panic"])
        )

        icon = Gio.ThemedIcon(name="media-playlist-repeat")
        self.seq_mode_butt_image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.seq_mode_butt.add(self.seq_mode_butt_image)
        self.seq_mode_butt.set_active(not mod.play_mode)
        self.seq_mode_butt.connect("clicked", self.on_playmode_toggled)
        self.seq_mode_butt.set_tooltip_markup(
            cfg.tooltip_markup2 % ("play mode", cfg.key["play_mode"])
        )
        self.seq_mode_butt_ignore_signal = False

        buttbox = Gtk.Box()
        self.seqlist_butts = buttbox
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

        self.timeline_view = TimelineView()
        mod.timeline_view = self.timeline_view

        self.timeline_box.pack2(self.timeline_view, True, True)
        self.timeline_box.set_position(cfg.timeline_position_y)

        self.vbox.pack_start(self.hbox, True, True, 0)
        self._status_bar = StatusBar()
        self.vbox.pack_end(self._status_bar, False, True, 0)
        self.vbox.set_orientation(Gtk.Orientation.VERTICAL)

        self.add(self.vbox)

        self.set_default_size(*cfg.mainwin_size)
        self.show_all()

        self.sequence_view._sv.grab_focus()

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

        mod.should_save = False
        self.add_tick_callback(self.tick)

    def on_destroy(self, wdg, param):
        if not mod.should_save:
            return

        if not cfg.ask_quit:
            return

        dialog = Gtk.MessageDialog(
            self,
            0,
            Gtk.MessageType.QUESTION,
            Gtk.ButtonsType.OK_CANCEL,
            "Quit without saving?",
        )

        rt = dialog.run()
        dialog.destroy()
        if rt == Gtk.ResponseType.CANCEL:
            return True

    def tick(self, wdg, param):
        mod.cdaemon.tick()
        self.time_display.set_markup(
            """<span font_desc="Roboto bold" font_family="monospace" size="x-large">%s</span>"""
            % mod.time
        )
        if self.transport_switch.props.state != mod.transport:
            self.transport_switch.props.state = mod.transport

        if not self._status_bar.portpopover:
            self._status_bar.portpopover = PortConfigPopover(self._status_bar)
            self._status_bar.portpopover.set_pointing_to(
                self._status_bar.portpopover_rect
            )

            show_pop = True
            for prt in mod.ports:
                if prt.mine:
                    if prt.connections:
                        show_pop = False

            if show_pop and cfg.port_popup:
                self._status_bar.portpopover.pop()

        if mod.ports_changed:
            refresh_connections(mod, cfg)
            if self._status_bar.portpopover.pooped:
                self._status_bar.portpopover.refresh()

        if mod.switch_req:
            v = self._status_bar.pulse.intensity(mod[0].pos)
            if v < 0.2:
                for w in self.seq_mode_butt.get_children():
                    self.seq_mode_butt.remove(w)
            else:
                ch = self.seq_mode_butt.get_children()
                if not ch:
                    self.seq_mode_butt.add(self.seq_mode_butt_image)
        else:
            ch = self.seq_mode_butt.get_children()
            if not ch:
                self.seq_mode_butt.add(self.seq_mode_butt_image)

        return 1

    def on_seq_mode_butt_draw(self, wdg, ctx):
        ctx.set_source_rgb(0, 0, 0)
        srf = ctx.get_target()

        w = srf.get_width()
        h = srf.get_height()
        ctx.rectangle(0, 0, w, h)
        ctx.fill()

    def on_start_button_activate(self, switch):
        mod.play = 1

    def on_stop_button_activate(self, switch):
        if not mod.play:
            npos = 0
            tl = mod.timeline

            if tl.loop.active:
                if tl.pos == 0:
                    npos = tl.loop.start
                if tl.pos > tl.loop.start:
                    npos = tl.loop.start

            mod.reset()
            if npos:
                tl.pos = npos

        mod.play = False

    def on_seq_add_butt_clicked(self, butt):
        self.sequence_view.seq_add()

    def on_transport_switch(self, wdg, state):
        mod.transport = state

    def on_butt_panic_pressed(self, butt):
        mod.panic(True)

    def on_butt_panic_released(self, butt):
        mod.unpanic()

    def on_playmode_toggled(self, butt):
        if self.seq_mode_butt_ignore_signal:
            return

        mod.play_mode = not butt.get_active()

    def hide_timeline(self):
        if not self.timeline_visible:
            return

        self.timeline_box.hide()

        self.timeline_visible = False
        cfg.timeline_show = False

    def show_timeline(self):
        if self.timeline_visible:
            return

        if 1 == len(self.hbox.get_children()):
            self.hbox.pack2(self.timeline_box, False, True)
            self.hbox.set_position(
                self.get_window().get_width() - cfg.timeline_position_x
            )

        self.hbox.set_wide_handle(True)
        self.timeline_visible = True
        self.timeline_box.show_all()
        cfg.timeline_show = True

    def hide_console(self):
        if not Console:
            return

        if not mod.console_visible:
            return

        self.console.hide()
        mod.console_visible = False
        self.sequence_view.auto_scroll_req = True

    def show_console(self):
        if not Console:
            return

        if mod.console_visible:
            return

        if 1 == len(self.seqbox.get_children()):
            self.seqbox.pack2(self.console, True, True)
            self.seqbox.set_position(
                self.get_window().get_height() * cfg.console_position
            )

        mod.console_visible = True
        self.seqbox.set_wide_handle(True)
        self.sequence_view.auto_scroll_req = True
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
            return True

        if cfg.key["panic"].matches(event):
            if not mod.is_panicking:
                mod.panic(True)
            return True

        if cfg.key["play_mode"].matches(event):
            self.seq_mode_butt.props.active = not self.seq_mode_butt.props.active
            return True

        return False

    def on_key_release(self, wdg, event):
        if cfg.key["panic"].matches(event):
            mod.unpanic()
            return True

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

    def load(self, filename, append=False):
        if not append:
            self.set_header_from_filename(None)

        if not self.sequence_view.load(filename, append):
            return False

        mod.pnq_hack = cfg.pnq_hack
        mod.inception = cfg.inception
        lfn = self.app.fixfn_backup(filename)
        if not append:
            self.last_filename = lfn
            self.set_header_from_filename(lfn)
        return True

    def gui_next_seq(self):
        mod.seqlist._highlight = -1

        ind = self.sequence_view.seq.index

        if type(ind) is tuple:
            ind = mod.timeline.strips[ind[1]].col

        if len(mod) > ind + 1:
            self.sequence_view.switch(ind + 1)
        else:
            self.sequence_view.switch(0)

        mod.curr_seq = self.sequence_view.seq.index
        mod.seqlist.redraw()

    def gui_prev_seq(self):
        mod.seqlist._highlight = -1

        ind = self.sequence_view.seq.index

        if type(ind) is tuple:
            ind = mod.timeline.strips[ind[1]].col + 1

        if ind > 0:
            self.sequence_view.switch(ind - 1)
        else:
            self.sequence_view.switch(len(mod) - 1)

        mod.curr_seq = self.sequence_view.seq.index
        mod.seqlist.redraw()

    def gui_del_seq(self, seq_id):
        # open from matrix
        if type(seq_id) is int:
            if len(mod) < 2:
                return

            curr = (
                mod.curr_seq
                if type(mod.curr_seq) is int
                else mod.timeline.strips[mod.curr_seq[1]].col
            )

            nxt = curr
            if seq_id < curr:
                nxt = max(nxt - 1, 0)

            if nxt == len(mod) - 1:
                nxt = max(nxt - 1, 0)

            if curr == seq_id:
                if curr < len(mod) - 1:
                    self.sequence_view.switch(curr + 1)
                else:
                    self.sequence_view.switch(curr - 1)

                self.gui_del_seq(curr)
                return

            # remove cached trks from substrips
            for strp in mod.timeline.strips:
                if strp.col == seq_id:
                    for trk in strp.seq:
                        if int(trk) in self.sequence_view.trk_cache:
                            del self.sequence_view.trk_cache[int(trk)]

                        if int(trk) in self.sequence_view.prop_view.trk_prop_cache:
                            del self.sequence_view.prop_view.trk_prop_cache[int(trk)]

            for trk in mod[seq_id]:
                if int(trk) in self.sequence_view.trk_cache:
                    del self.sequence_view.trk_cache[int(trk)]

                if int(trk) in self.sequence_view.prop_view.trk_prop_cache:
                    del self.sequence_view.prop_view.trk_prop_cache[int(trk)]

            mod.cdaemon.remove_seq(mod[seq_id])
            mod.del_sequence(seq_id)
            self.sequence_view.switch(nxt)
            mod.timeline.update()
            mod.thumbmanager.clear()
            return True
        elif type(seq_id) is tuple:
            curr = mod.curr_seq
            if type(curr) is tuple:
                if curr[1] == seq_id[1]:
                    strp = mod.timeline.strips[curr[1]]
                    prev = strp.prev_id
                    if prev:
                        mod.mainwin.sequence_view.switch(prev)
                    else:
                        mod.mainwin.sequence_view.switch(strp.col)

            self.timeline_view.curr_col = -1
            self.timeline_view.curr_strip_id = -1

            for trk in mod[seq_id]:
                if int(trk) in self.sequence_view.trk_cache:
                    del self.sequence_view.trk_cache[int(trk)]

                if int(trk) in self.sequence_view.prop_view.trk_prop_cache:
                    del self.sequence_view.prop_view.trk_prop_cache[int(trk)]

            mod.timeline.strips.delete(seq_id[1])
            mod.thumbmanager.clear()

    def gui_del_trk(seq_id, trk_id):
        print("gui_del_trk", seq_id, trk_id)
