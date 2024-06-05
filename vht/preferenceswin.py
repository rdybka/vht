# preferenceswin.py - vahatraker
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
import os

from vht.notebooklabel import NotebookLabel
from vht.configuration import Configuration
from vht.midimapview import MidiMapView
from vht.portconfig import refresh_connections

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, Gdk


class PreferencesWin(Gtk.Window):
    def __init__(self, parent, mod, cfg, app):
        super(PreferencesWin, self).__init__()
        self.set_default_size(cfg.mainwin_size[0] / 2, 0)
        self.cfg = cfg
        self.mod = mod
        self.parent = parent
        self.def_cfg = Configuration()

        self.set_transient_for(self.parent)
        self.set_application(app)
        self.set_resizable(False)
        self.set_modal(True)

        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", self.on_destroy)

        self.hb = Gtk.HeaderBar()
        self.hb.set_title("Preferences")
        self.hb.set_show_close_button(True)
        self.set_titlebar(self.hb)
        self.hb.show_all()

        self.st = Gtk.Stack()
        self.st.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.box1 = self.create_box1()
        self.box2 = self.create_box2()
        self.box3 = self.create_box3()
        self.box4 = self.create_box4()
        self.box5 = self.create_box5()

        self.st.add_titled(self.box1, "lnf", "Look & Feel")
        self.st.add_titled(self.box2, "mid", "MIDI")
        self.st.add_titled(self.box3, "adv", "Advanced")
        self.st.add_titled(self.box4, "bck", "Backup")
        self.st.add_titled(self.box5, "oth", "Tweaks")

        self.sbar = Gtk.StackSidebar()
        self.sbar.set_stack(self.st)

        box = Gtk.Box()
        box.pack_start(self.sbar, True, True, 0)
        box.pack_end(self.st, True, True, 0)

        self.add(box)
        self.show_all()

        self.midi_in_cmb.connect("changed", self.on_combo_midi_input_changed)
        self.midi_out_cmb.connect("changed", self.on_combo_midi_output_changed)
        self.st.set_visible_child_name("lnf")

    def on_destroy(self, wdg):
        self.mod.gui_midi_capture = False
        self.cfg.save()
        midig = []
        for val in self.cfg.midi_in.values():
            if val:
                midig.append(val)

        self.mod.set_midi_record_ignore(midig)

    def cbutt(self, col, data):
        butt = Gtk.ColorButton()
        butt.set_use_alpha(False)
        butt.set_rgba(col)
        butt.connect("notify::rgba", self.on_colour_activated, data)
        return butt

    def fbutt(self, fnt, data):
        butt = Gtk.FontButton()
        butt.set_show_style(False)
        butt.set_filter_func(self.font_filter, data)
        butt.set_level(Gtk.FontChooserLevel.FAMILY)

        butt.set_font("%s" % fnt)
        butt.connect("notify::font", self.on_font_activated, data)
        butt.set_hexpand(True)

        return butt

    def create_slider(self, digits, value, low, hi, data):
        scale = Gtk.Scale()
        scale.set_range(low, hi)
        scale.set_digits(digits)
        scale.set_value(value)
        scale.connect("value-changed", self.on_scale_changed, data)
        return scale

    def create_frame(self, name, mrg):
        frame = Gtk.Frame.new(name)
        grid = Gtk.Grid()
        grid.set_margin_top(mrg)
        grid.set_margin_bottom(mrg)
        grid.set_margin_left(mrg)
        grid.set_margin_right(mrg)
        grid.set_hexpand(True)
        frame.add(grid)
        return frame, grid

    def create_box1(self):
        grid = Gtk.Grid()
        mrg = 5
        grid.set_margin_top(mrg)
        grid.set_margin_bottom(mrg)
        grid.set_margin_left(mrg)
        grid.set_margin_right(mrg)

        bx = Gtk.Box()
        lab = Gtk.Label.new("Dark theme")

        sw = Gtk.Switch()
        sw.set_active(self.cfg.dark_theme)
        sw.connect("state-set", self.on_dark_mode_switch)
        sw.set_tooltip_markup(self.cfg.tooltip_markup % ("may not be honoured"))
        bx.pack_start(lab, False, False, 0)
        bx.pack_end(sw, False, False, 0)
        grid.attach(bx, 0, 0, 1, 1)

        bx = Gtk.Box()
        lab = Gtk.Label.new("Popup transition")

        sw = Gtk.Switch()
        sw.set_active(self.cfg.popup_transition)
        sw.connect("state-set", self.on_popup_transition_switch)
        bx.pack_start(lab, False, False, 0)
        bx.pack_end(sw, False, False, 0)
        grid.attach(bx, 0, 1, 1, 1)

        bx = Gtk.Box()
        lab = Gtk.Label.new("Opacity")
        lab.set_xalign(0)
        bx.set_hexpand(True)
        self.opslider = self.create_slider(2, self.cfg.window_opacity, 0.05, 1, 3)
        bx.pack_start(lab, True, True, 0)
        bx.pack_end(self.opslider, True, True, 0)
        grid.attach(bx, 0, 2, 1, 1)

        fr, gr = self.create_frame("Sequence", mrg)
        scbutt = self.cbutt(Gdk.RGBA(*self.cfg.colour, 1), 0)
        sfbutt = self.fbutt(self.cfg.seq_font, 0)
        sslider = self.create_slider(2, self.cfg.seq_spacing, 0.5, 2, 0)
        gr.attach(scbutt, 0, 0, 1, 1)
        gr.attach(sfbutt, 1, 0, 1, 1)
        gr.attach(sslider, 0, 1, 2, 1)
        grid.attach(fr, 0, 3, 1, 1)

        fr, gr = self.create_frame("Matrix", mrg)
        scbutt = self.cbutt(Gdk.RGBA(*self.cfg.mixer_colour, 1), 1)
        sfbutt = self.fbutt(self.cfg.mixer_font, 1)
        gr.attach(scbutt, 1, 0, 1, 1)
        gr.attach(sfbutt, 2, 0, 1, 1)
        grid.attach(fr, 0, 4, 1, 1)

        fr, gr = self.create_frame("Timeline", mrg)
        scbutt = self.cbutt(Gdk.RGBA(*self.cfg.timeline_colour, 1), 2)
        sfbutt = self.fbutt(self.cfg.timeline_font, 2)
        gr.attach(scbutt, 1, 0, 1, 1)
        gr.attach(sfbutt, 2, 0, 1, 1)
        grid.attach(fr, 0, 5, 1, 1)

        fr, gr = self.create_frame("Console", mrg)
        scbutt = self.cbutt(Gdk.RGBA(*self.cfg.console_colour, 1), 3)
        sfbutt = self.fbutt(self.cfg.console_font, 3)
        gr.attach(scbutt, 1, 0, 1, 1)
        gr.attach(sfbutt, 2, 0, 1, 1)
        grid.attach(fr, 0, 6, 1, 1)

        bx = Gtk.Box()

        bx.pack_start(Gtk.Label.new("star"), True, True, 0)
        scbutt = self.cbutt(Gdk.RGBA(*self.cfg.star_colour, 1), 4)
        bx.pack_start(scbutt, False, False, 0)

        scbutt = self.cbutt(Gdk.RGBA(*self.cfg.mandy_colour, 1), 6)
        bx.pack_end(scbutt, False, False, 0)
        bx.pack_end(Gtk.Label.new("mandy"), True, True, 0)

        scbutt = self.cbutt(Gdk.RGBA(*self.cfg.record_colour, 1), 5)
        bx.pack_end(scbutt, False, False, 0)
        bx.pack_end(Gtk.Label.new("rec"), True, True, 0)
        grid.attach(bx, 0, 7, 1, 1)

        cmb = Gtk.ComboBoxText()
        cmb.append_text("none")
        cmb.append_text("not too rough")
        cmb.append_text("hurt me plenty")

        v = 0
        if self.cfg.track_prop_mouseover:
            v = 1

        if self.cfg.notebook_mouseover:
            v = 2

        cmb.set_active(v)
        cmb.connect("changed", self.on_combo_mouseover_changed)
        # gr.attach(cmb, 0, 0, 1, 1)
        bx = Gtk.Box()
        lab = Gtk.Label.new("Mouse-over")
        bx.pack_start(lab, False, False, 0)
        bx.pack_end(cmb, False, True, 0)
        grid.attach(bx, 0, 8, 1, 1)

        return grid

    def create_box2(self):
        grid = Gtk.Grid()
        mrg = 5
        grid.set_margin_top(mrg)
        grid.set_margin_bottom(mrg)
        grid.set_margin_left(mrg)
        grid.set_margin_right(mrg)

        fr, gr = self.create_frame("Default input", mrg)
        cmb = Gtk.ComboBoxText()
        cmb.set_hexpand(False)
        cmb.append_text("none")
        pp = []
        pretty = {}
        for prt in self.mod.ports:
            if prt.type == "midi" and not prt.mine and prt.output:
                pp.append(prt.name)
                pretty[prt.name] = prt.pname

        dinp = self.cfg.midi_default_input
        if dinp and dinp not in pp:
            pp.append(dinp)

        for prt in pp:
            cmb.append(prt, pretty[prt][:33] if prt in pretty else prt)

        dinp = self.cfg.midi_default_input
        if dinp and dinp in pp:
            cmb.set_active(pp.index(dinp) + 1)
        else:
            cmb.set_active(0)

        self.midi_in_cmb = cmb
        gr.attach(cmb, 0, 0, 1, 1)
        grid.attach(fr, 0, 0, 1, 1)

        fr, gr = self.create_frame("Default output", mrg)
        cmb = Gtk.ComboBoxText()
        cmb.set_hexpand(False)
        cmb.append_text("none")

        pp = []
        pretty = {}
        for prt in self.mod.ports:
            if prt.type == "midi" and not prt.mine and prt.input:
                pp.append(prt.name)
                pretty[prt.name] = prt.pname

        doutp = self.cfg.midi_default_output
        if doutp and doutp not in pp:
            pp.append(doutp)

        for prt in pp:
            cmb.append(prt, pretty[prt][:33] if prt in pretty else prt)

        doutp = self.cfg.midi_default_output
        if doutp and doutp in pp:
            cmb.set_active(pp.index(doutp) + 1)
        else:
            cmb.set_active(0)

        self.midi_out_cmb = cmb
        gr.attach(cmb, 0, 0, 1, 1)
        grid.attach(fr, 0, 1, 1, 1)

        fr, gr = self.create_frame("Map", mrg)
        self.midimap_view = MidiMapView(self)
        gr.attach(self.midimap_view, 0, 0, 1, 1)
        grid.attach(fr, 0, 2, 1, 1)

        return grid

    def create_entry(self, txt, maxlen, purpose=Gtk.InputPurpose.FREE_FORM):
        ent = Gtk.Entry()
        ent.set_input_purpose(purpose)
        if maxlen:
            ent.set_width_chars(maxlen)
            ent.set_max_length(maxlen)

        ent.set_text(txt)
        ent.connect("changed", self.on_entry_changed)
        return ent

    def create_reset_butt(self, data):
        butt = Gtk.Button()
        butt.set_label("reset")
        butt.connect("clicked", self.on_reset_butt_clicked, data)
        return butt

    def create_box3(self):
        grid = Gtk.Grid()
        mrg = 5
        grid.set_margin_top(mrg)
        grid.set_margin_bottom(mrg)
        grid.set_margin_left(mrg)
        grid.set_margin_right(mrg)

        bx = Gtk.Box()
        lab = Gtk.Label.new("Confirm quit")

        sw = Gtk.Switch()
        sw.set_active(self.cfg.ask_quit)
        sw.connect("state-set", self.on_ask_quit_switch)
        sw.set_tooltip_markup(self.cfg.tooltip_markup % ("when unsaved changes"))
        bx.pack_start(lab, False, False, 0)
        bx.pack_end(sw, False, False, 0)
        grid.attach(bx, 0, 0, 1, 1)

        fr, gr = self.create_frame("Quick controls", mrg)

        bx = Gtk.Box()
        bx.set_hexpand(True)
        bx.pack_start(Gtk.Label.new("desc"), False, False, 0)
        self.qc_desc_ent = self.create_entry(self.cfg.quick_controls_desc, 10)
        bx.pack_end(self.qc_desc_ent, False, False, 0)
        gr.attach(bx, 0, 0, 1, 1)

        bx = Gtk.Box()
        bx.set_hexpand(True)
        bx.pack_start(Gtk.Label.new("ctrl1"), False, False, 0)
        self.qc_1_ctrl_ent = self.create_entry(
            str(self.cfg.quick_control_1_ctrl), 3, Gtk.InputPurpose.DIGITS
        )
        self.qc_1_def_slider = self.create_slider(
            0, self.cfg.quick_control_1_def, 0, 127, 1
        )
        bx.pack_start(self.qc_1_ctrl_ent, False, False, 0)
        bx.pack_end(self.qc_1_def_slider, True, True, 0)
        gr.attach(bx, 0, 1, 1, 1)

        bx = Gtk.Box()
        bx.set_hexpand(True)
        bx.pack_start(Gtk.Label.new("ctrl2"), False, False, 0)
        self.qc_2_ctrl_ent = self.create_entry(
            str(self.cfg.quick_control_2_ctrl), 3, Gtk.InputPurpose.DIGITS
        )
        self.qc_2_def_slider = self.create_slider(
            0, self.cfg.quick_control_2_def, 0, 127, 2
        )
        bx.pack_start(self.qc_2_ctrl_ent, False, False, 0)
        bx.pack_end(self.qc_2_def_slider, True, True, 0)
        gr.attach(bx, 0, 2, 1, 1)

        grid.attach(fr, 0, 2, 1, 1)

        fr, gr = self.create_frame("Midi export SMPTE", mrg)

        cmb = Gtk.ComboBoxText()
        cmb.append_text("30fps")
        cmb.append_text("25fps")

        cmb.set_active(self.cfg.render_timecode)
        cmb.connect("changed", self.on_combo_rendertc_changed)

        tick_slider = self.create_slider(0, self.cfg.render_ticks, 40, 120, 4)

        tick_slider.add_mark(40, Gtk.PositionType.TOP)
        tick_slider.add_mark(80, Gtk.PositionType.TOP)
        tick_slider.add_mark(100, Gtk.PositionType.TOP)
        tick_slider.add_mark(120, Gtk.PositionType.TOP)

        bx = Gtk.Box()
        bx.set_hexpand(True)
        bx.pack_start(cmb, False, False, 0)
        bx.pack_end(Gtk.Label.new("ticks/frame"), False, False, 0)

        bx.pack_end(tick_slider, True, True, 0)

        gr.attach(bx, 0, 0, 1, 1)
        grid.attach(fr, 0, 3, 1, 1)

        fr, gr = self.create_frame("White piano keys", mrg)
        self.piano_white_keys_ent = self.create_entry(self.cfg.piano_white_keys, 14)
        rsbutt = self.create_reset_butt(2)
        bx = Gtk.Box()
        bx.set_hexpand(True)
        bx.pack_start(self.piano_white_keys_ent, False, False, 0)
        bx.pack_end(rsbutt, False, False, 0)

        gr.attach(bx, 0, 0, 1, 1)
        grid.attach(fr, 0, 4, 1, 1)

        fr, gr = self.create_frame("Black piano keys", mrg)
        self.piano_black_keys_ent = self.create_entry(self.cfg.piano_black_keys, 10)
        rsbutt = self.create_reset_butt(1)
        bx = Gtk.Box()
        bx.set_hexpand(True)
        bx.pack_start(self.piano_black_keys_ent, False, False, 0)
        bx.pack_end(rsbutt, False, False, 0)

        gr.attach(bx, 0, 0, 1, 1)
        grid.attach(fr, 0, 5, 1, 1)

        fr, gr = self.create_frame("Velocity keys", mrg)
        self.velocity_keys_ent = self.create_entry(self.cfg.velocity_keys, 7)
        rsbutt = self.create_reset_butt(0)
        bx = Gtk.Box()
        bx.set_hexpand(True)
        bx.pack_start(self.velocity_keys_ent, False, False, 0)
        bx.pack_end(rsbutt, False, False, 0)

        gr.attach(bx, 0, 0, 1, 1)
        grid.attach(fr, 0, 6, 1, 1)

        return grid

    def create_box4(self):
        grid = Gtk.Grid()
        mrg = 5
        grid.set_margin_top(mrg)
        grid.set_margin_bottom(mrg)
        grid.set_margin_left(mrg)
        grid.set_margin_right(mrg)

        fr, gr = self.create_frame("Keep backups", mrg)
        nbck_adj = Gtk.Adjustment(1, 0, 99, 1.0, 1.0)
        nbck_button = Gtk.SpinButton()
        nbck_button.set_adjustment(nbck_adj)
        nbck_adj.set_value(self.cfg.n_backups)

        nbck_adj.connect("value-changed", self.on_nbck_value_changed)

        gr.attach(nbck_button, 0, 0, 1, 1)

        grid.attach(fr, 0, 0, 1, 1)

        fr, gr = self.create_frame("Autosave", mrg)
        bx = Gtk.Box()
        bx.set_hexpand(True)
        lab = Gtk.Label.new("when deleting sequence")

        sw = Gtk.Switch()
        sw.set_active(self.cfg.autosave_seq)
        sw.connect("state-set", self.on_autosave_seq_switch)

        bx.pack_start(lab, False, False, 0)
        bx.pack_end(sw, False, False, 0)
        gr.attach(bx, 0, 0, 1, 1)

        bx = Gtk.Box()
        bx.set_hexpand(True)
        lab = Gtk.Label.new("when deleting track")

        sw = Gtk.Switch()
        sw.set_active(self.cfg.autosave_trk)
        sw.connect("state-set", self.on_autosave_trk_switch)

        bx.pack_start(lab, False, False, 0)
        bx.pack_end(sw, False, False, 0)
        gr.attach(bx, 0, 1, 1, 1)
        grid.attach(fr, 0, 3, 1, 1)

        return grid

    def create_box5(self):
        grid = Gtk.Grid()
        mrg = 5
        grid.set_margin_top(mrg)
        grid.set_margin_bottom(mrg)
        grid.set_margin_left(mrg)
        grid.set_margin_right(mrg)

        bx = Gtk.Box()
        lab = Gtk.Label.new("New tracks on left")

        sw = Gtk.Switch()
        sw.set_active(self.cfg.new_tracks_left)
        sw.connect("state-set", self.on_new_tracks_left_switch)
        bx.pack_start(lab, False, False, 0)
        bx.pack_end(sw, False, False, 0)
        grid.attach(bx, 0, 0, 1, 1)

        bx = Gtk.Box()
        lab = Gtk.Label.new("Empty track in new seq")

        sw = Gtk.Switch()
        sw.set_active(self.cfg.new_seqs_with_tracks)
        sw.connect("state-set", self.on_new_seqs_tracks_switch)
        bx.pack_start(lab, False, False, 0)
        bx.pack_end(sw, False, False, 0)
        grid.attach(bx, 0, 1, 1, 1)

        bx = Gtk.Box()
        lab = Gtk.Label.new("Pop up ports")
        bx.set_hexpand(True)

        sw = Gtk.Switch()
        sw.set_active(self.cfg.port_popup)
        sw.connect("state-set", self.on_port_popup_switch)
        sw.set_tooltip_markup(self.cfg.tooltip_markup % ("if no connections active"))
        bx.pack_start(lab, False, False, 0)
        bx.pack_end(sw, False, False, 0)
        grid.attach(bx, 0, 2, 1, 1)

        bx = Gtk.Box()
        lab = Gtk.Label.new("pnq_hack")
        bx.set_hexpand(True)

        sw = Gtk.Switch()
        sw.set_active(self.cfg.pnq_hack)
        sw.connect("state-set", self.on_pnq_hack_switch)
        sw.set_tooltip_markup(
            self.cfg.tooltip_markup % ("sending c16:g-9 will panik given port")
        )
        bx.pack_start(lab, False, False, 0)
        bx.pack_end(sw, False, False, 0)
        grid.attach(bx, 0, 3, 1, 1)

        bx = Gtk.Box()
        lab = Gtk.Label.new("inception")
        bx.set_hexpand(True)

        sw = Gtk.Switch()
        sw.set_active(self.cfg.inception)
        sw.connect("state-set", self.on_inception_switch)
        sw.set_tooltip_markup(
            self.cfg.tooltip_markup % ("p15 will feed back to triggers")
        )
        bx.pack_start(lab, False, False, 0)
        bx.pack_end(sw, False, False, 0)
        grid.attach(bx, 0, 4, 1, 1)

        return grid

    def on_nbck_value_changed(self, adj):
        self.cfg.n_backups = int(adj.get_value())

    def font_filter(self, family, face, data):
        if not family.is_monospace():
            return False

        return True

    def on_reset_butt_clicked(self, wdg, data):
        if data == 0:
            self.velocity_keys_ent.set_text(self.def_cfg.velocity_keys)
        elif data == 1:
            self.piano_black_keys_ent.set_text(self.def_cfg.piano_black_keys)
        elif data == 2:
            self.piano_white_keys_ent.set_text(self.def_cfg.piano_white_keys)

    def on_entry_changed(self, wdg):
        txt = wdg.get_text()

        if wdg == self.velocity_keys_ent:
            self.cfg.velocity_keys = txt
        elif wdg == self.piano_white_keys_ent:
            self.cfg.piano_white_keys = txt
        elif wdg == self.piano_black_keys_ent:
            self.cfg.piano_black_keys = txt
        elif wdg == self.qc_desc_ent:
            self.cfg.quick_controls_desc = txt
        elif wdg == self.qc_1_ctrl_ent:
            if txt.isnumeric():
                self.cfg.quick_control_1_ctrl = max(0, min(127, int(txt)))
        elif wdg == self.qc_2_ctrl_ent:
            if txt.isnumeric():
                self.cfg.quick_control_2_ctrl = max(0, min(127, int(txt)))

    def on_colour_activated(self, wdg, prm, data):
        rgba = wdg.get_rgba()
        if data == 0:
            self.cfg.colour = (rgba.red, rgba.green, rgba.blue)
            self.parent.sequence_view.zoom(1)
            self.parent.sequence_view.zoom(-1)
        elif data == 1:
            self.cfg.mixer_colour = (rgba.red, rgba.green, rgba.blue)
        elif data == 2:
            self.cfg.timeline_colour = (rgba.red, rgba.green, rgba.blue)
        elif data == 3:
            self.cfg.console_colour = (rgba.red, rgba.green, rgba.blue)
            self.parent.console.refresh()
        elif data == 4:
            self.cfg.star_colour = (rgba.red, rgba.green, rgba.blue)
        elif data == 5:
            self.cfg.record_colour = (rgba.red, rgba.green, rgba.blue)
        elif data == 6:
            self.cfg.mandy_colour = (rgba.red, rgba.green, rgba.blue)

        self.cfg.save()

    def on_font_activated(self, wdg, prm, data):
        fdesc = wdg.get_font_desc()

        if data == 0:
            self.cfg.seq_font = "%s" % (fdesc.get_family())
            self.parent.sequence_view.zoom(1)
            self.parent.sequence_view.zoom(-1)
        elif data == 1:
            self.cfg.mixer_font = "%s" % (fdesc.get_family())
            self.parent.seqlist.zoom(1)
            self.parent.seqlist.zoom(-1)
        elif data == 2:
            self.cfg.timeline_font = "%s" % (fdesc.get_family())
            self.parent.timeline_view.on_configure(self.parent.timeline_view, 0)
        elif data == 3:
            self.cfg.console_font = "%s" % (fdesc.get_family())
            self.parent.console.refresh()

        self.cfg.save()

    def on_scale_changed(self, wdg, data):
        val = wdg.get_value()

        if data == 0:
            self.cfg.seq_spacing = val
            self.parent.sequence_view.zoom(1)
            self.parent.sequence_view.zoom(-1)
        if data == 1:
            self.cfg.quick_control_1_def = int(val)
        if data == 2:
            self.cfg.quick_control_2_def = int(val)
        if data == 3:
            self.parent.set_opacity(self.cfg.window_opacity)
            self.cfg.window_opacity = val
        if data == 4:
            self.cfg.render_ticks = int(val)

    def on_combo_midi_input_changed(self, wdg):
        self.cfg.midi_default_input = wdg.get_active_id() if wdg.get_active() else ""
        pc = self.mod.extras["portconfig"]
        if self.cfg.midi_default_input and self.cfg.midi_default_input not in pc["in"]:
            pc["in"].append(self.cfg.midi_default_input)

        refresh_connections(self.mod, self.cfg)
        if self.parent._status_bar.portpopover.pooped:
            self.parent._status_bar.portpopover.refresh()

    def on_combo_midi_output_changed(self, wdg):
        self.cfg.midi_default_output = wdg.get_active_id() if wdg.get_active() else ""
        pc = self.mod.extras["portconfig"]
        if (
            self.cfg.midi_default_output
            and self.cfg.midi_default_output not in pc["out"][0]
        ):
            pc["out"][0].append(self.cfg.midi_default_output)
        refresh_connections(self.mod, self.cfg)
        if self.parent._status_bar.portpopover.pooped:
            self.parent._status_bar.portpopover.refresh()

    def on_combo_rendertc_changed(self, wdg):
        v = wdg.get_active()
        self.cfg.render_timecode = v

    def on_combo_mouseover_changed(self, wdg):
        v = wdg.get_active()
        n = 0
        t = 0

        if v == 1:
            t = True
            n = False
        if v == 2:
            t = True
            n = True

        self.cfg.notebook_mouseover = n
        self.cfg.track_prop_mouseover = t

    def on_dark_mode_switch(self, wdg, prm):
        self.cfg.dark_theme = prm
        st = self.parent.get_settings()
        st.set_property("gtk-application-prefer-dark-theme", self.cfg.dark_theme)

    def on_popup_transition_switch(self, wdg, prm):
        self.cfg.popup_transition = prm

    def on_autosave_trk_switch(self, wdg, prm):
        self.cfg.autosave_trk = prm

    def on_autosave_seq_switch(self, wdg, prm):
        self.cfg.autosave_seq = prm

    def on_new_seqs_tracks_switch(self, wdg, prm):
        self.cfg.new_seqs_with_tracks = prm

    def on_new_tracks_left_switch(self, wdg, prm):
        self.cfg.new_tracks_left = prm

    def on_ask_quit_switch(self, wdg, prm):
        self.cfg.ask_quit = prm

    def on_port_popup_switch(self, wdg, prm):
        self.cfg.port_popup = prm

    def on_pnq_hack_switch(self, wdg, prm):
        self.cfg.pnq_hack = prm
        self.mod.pnq_hack = prm
        self.parent.sequence_view.zoom(1)
        self.parent.sequence_view.zoom(-1)

    def on_inception_switch(self, wdg, prm):
        self.cfg.inception = prm
        self.mod.inception = prm
        self.parent.sequence_view.zoom(1)
        self.parent.sequence_view.zoom(-1)

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
            return True
