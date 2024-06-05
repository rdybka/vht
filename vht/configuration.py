# configuration.py - vahatraker
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

from pathlib import Path
import configparser

import gi

gi.require_version("Gdk", "3.0")
from gi.repository import Gdk


class Configuration:
    def __init__(self):
        self.filename = None

        self.seq_font = "Monospace"
        self.console_font = "Monospace"
        self.mixer_font = "Monospace"
        self.timeline_font = "Monospace"

        self.seq_font_size = 18
        self.mixer_font_size = 16
        self.timeline_font_size = 12

        self.mixer_padding = 1.5
        self.seq_line_width = 1.0
        self.seq_spacing = 1.05
        self.status_bar_font_size = 24

        self.mainwin_size = (766, 423)

        self.console_scale = 1
        self.timeline_position_x = 200
        self.timeline_position_y = 120
        self.console_position = 0.5
        self.console_show = False
        self.timeline_show = True
        self.console_steal_stderr = True
        self.start_playing = True
        self.start_transport = False
        self.port_popup = True

        c = (0.6, 1.0, 1.0)
        self.colour = c

        c = (0.3, 1.0, 0.3)
        self.mixer_colour = c

        self.star_colour = (1, 1, 0)
        self.console_colour = self.star_colour
        self.timeline_colour = self.mixer_colour

        self.record_colour = (1.0, 0, 0)
        self.mandy_colour = self.colour
        self.mandy_crosshair_colour = self.record_colour

        self.popup_timeout = 0.5
        self.popup_transition = True

        self.intensity_background = 0.2
        self.intensity_txt = 0.9
        self.intensity_indicator = 0.75
        self.intensity_txt_highlight = 1.6
        self.intensity_lines = 0.9
        self.even_highlight = 1.4
        self.intensity_select = 0.7
        self.pointer_opacity = 1.0
        self.pointer_width = 5
        self.auto_scroll_delay = 0.05
        self.tooltip_markup = (
            """<span font_family="Monospace" size="medium">%s</span>"""
        )
        self.tooltip_markup2 = """<span font_family="Sans" size="large">%s\n</span><span font_family="Monospace" size="medium">%s</span>"""

        self.window_opacity = 1

        self.sequence_name_format = "s%02d"
        self.row_number_format = "%03d"

        self.velocity_editor_char_width = 8
        self.timeshift_editor_char_width = 8
        self.controllereditor_char_width = 8
        self.editor_row_height = 0.5

        self.drag_edit_divisor = 1.5
        self.default_velocity = 100

        self.octave = 4
        self.velocity = 100
        self.page_height = 16
        self.skip = 1

        self.select_button = 1
        self.delete_button = 3

        self.default_ctrl_name = "gm"

        self.dark_theme = True
        self.notebook_mouseover = False
        self.track_prop_mouseover = False

        self.quick_controls_desc = "vol/pan"
        self.quick_control_1_ctrl = 7
        self.quick_control_1_def = 100
        self.quick_control_2_ctrl = 10
        self.quick_control_2_def = 64

        self.new_tracks_left = False
        self.new_seqs_with_tracks = True

        self.default_seq_length = 16
        self.controller_resolution = 8
        self.pnq_hack = True
        self.inception = True

        self.last_load_path = ""
        self.last_save_path = ""
        self.save_indication_time = 0.23
        self.track_indication_time = 0.02

        self.timeline_delete_time = 0.25
        self.timeline_hint_time = 0.25

        self.render_mode = 2
        self.render_meter = 0
        self.render_secs = 5
        self.render_format = "flac"
        self.render_midi = True
        self.render_timecode = 0
        self.render_ticks = 120
        self.render_folder = str(Path.home())

        self.key = {
            # sequenceview		shift, ctrl, alt
            "quit": cfgkey("q", False, True, False),
            "toggle_timeline": cfgkey("Tab", False, True, False),
            "toggle_console": cfgkey("grave", False, False, False),
            "toggle_transport": cfgkey("t", False, False, True),
            "play": cfgkey("Return", False, False, False),
            "reset": cfgkey("Escape", False, False, False),
            "multi_record": cfgkey("space", False, True, False),
            "record": cfgkey("space", False, False, False),
            "fullscreen": cfgkey("Return", False, False, True),
            "exit_edit": cfgkey("Escape", False, False, False),
            "undo": cfgkey("z", False, True, False),
            "save": cfgkey("s", False, True, False),
            "load": cfgkey("o", False, True, False),
            "zoom_in": cfgkey("KP_Add", False, True, False),
            "zoom_out": cfgkey("KP_Subtract", False, True, False),
            "skip_up": cfgkey("KP_Add", False, False, False),
            "skip_down": cfgkey("KP_Subtract", False, False, False),
            "bpm_up": cfgkey("Up", True, True, False),
            "bpm_down": cfgkey("Down", True, True, False),
            "bpm_10_up": cfgkey("Page_Up", True, True, False),
            "bpm_10_down": cfgkey("Page_Down", True, True, False),
            "bpm_frac_up": cfgkey("Right", True, True, False),
            "bpm_frac_down": cfgkey("Left", True, True, False),
            "rpb_up": cfgkey("KP_Add", True, True, False),
            "rpb_down": cfgkey("KP_Subtract", True, True, False),
            "octave_up": cfgkey("KP_Multiply", False, False, False),
            "octave_down": cfgkey("KP_Divide", False, False, False),
            "def_port_up": cfgkey("KP_Multiply", True, True, False),
            "def_port_down": cfgkey("KP_Divide", True, True, False),
            "follow": cfgkey("f", False, False, False),
            "panic": cfgkey("p", True, True, True),
            "play_mode": cfgkey("p", False, True, False),
            "note_off": cfgkey("backslash", False, False, False),
            "track_add": cfgkey("t", False, True, False),
            "track_del": cfgkey("d", False, True, False),
            "track_expand": cfgkey("r", False, True, False),
            "track_shrink": cfgkey("e", False, True, False),
            "track_move_right": cfgkey("Right", False, True, False),
            "track_move_left": cfgkey("Left", False, True, False),
            "track_move_last": cfgkey("End", False, True, False),
            "track_move_first": cfgkey("Home", False, True, False),
            "track_clear": cfgkey("d", True, False, False),
            "track_clone": cfgkey("n", True, True, False),
            "track_resend_patch": cfgkey("r", False, False, True),
            "sequence_add": cfgkey("n", False, True, False),
            "sequence_play_mode": cfgkey("", False, False, False),
            "sequence_next": cfgkey("period", False, True, False),
            "sequence_prev": cfgkey("comma", False, True, False),
            "sequence_move_right": cfgkey("greater", True, True, False),
            "sequence_move_left": cfgkey("less", True, True, False),
            "sequence_double": cfgkey("y", False, True, False),
            "sequence_halve": cfgkey("u", False, True, False),
            "strip_double": cfgkey("y", True, True, False),
            "strip_halve": cfgkey("u", True, True, False),
            "sequence_delete": cfgkey("d", True, True, False),
            "sequence_clone": cfgkey("l", True, True, False),
            "sequence_loop": cfgkey("l", False, False, False),
            "sequence_replace": cfgkey("r", True, True, False),
            "select_all": cfgkey("a", False, True, False),
            "copy": cfgkey("c", False, True, False),
            "cut": cfgkey("x", False, True, False),
            "paste": cfgkey("v", False, True, False),
            "paste_over": cfgkey("v", True, True, False),
            "delete": cfgkey("Delete", False, False, False),
            "pull": cfgkey("Delete", False, True, False),
            "push": cfgkey("Insert", False, True, False),
            "transp_up": cfgkey("Up", False, True, False),
            "transp_down": cfgkey("Down", False, True, False),
            "transp_12_up": cfgkey("Page_Up", False, True, False),
            "transp_12_down": cfgkey("Page_Down", False, True, False),
            "velocity_up": cfgkey("Up", False, False, True),
            "velocity_down": cfgkey("Down", False, False, True),
            "velocity_10_up": cfgkey("Page_Up", False, False, True),
            "velocity_10_down": cfgkey("Page_Down", False, False, True),
            "channel_up": cfgkey("KP_Add", True, False, True),
            "channel_down": cfgkey("KP_Subtract", True, False, True),
            "port_up": cfgkey("KP_Multiply", True, False, True),
            "port_down": cfgkey("KP_Divide", True, False, True),
            "hold_editor": cfgkey("Control_L", False, False, False),
            "node_snap": cfgkey("Control_L", False, False, False),
            "velocity_line": cfgkey("Shift_L", False, False, False),
            "toggle_notes": cfgkey("1", False, True, False),
            "toggle_time": cfgkey("2", False, True, False),
            "toggle_pitch": cfgkey("3", False, True, False),
            "toggle_controllers": cfgkey("4", False, True, False),
            "toggle_probs": cfgkey("5", False, True, False),
            # controllereditor
            "link": cfgkey("l", False, True, False),
            "doodle_copy": cfgkey("c", True, True, False),
            "doodle_cut": cfgkey("x", True, True, False),
            "doodle_paste": cfgkey("v", True, True, False),
            "doodle_delete": cfgkey("Delete", True, True, False),
            "doodle_render": cfgkey("Insert", True, True, False),
            "ctrl_one_up": cfgkey("Right", True, False, False),
            "ctrl_one_down": cfgkey("Left", True, False, False),
            # mandy
            "mandy_active": cfgkey("Return", False, False, False),
            "mandy_show_info": cfgkey("i", False, False, False),
            "mandy_show_crosshair": cfgkey("c", False, False, False),
            "mandy_direction": cfgkey("d", False, False, False),
            "mandy_switch_mode": cfgkey("j", False, False, False),
            "mandy_pick_julia": cfgkey("e", False, False, False),
            "mandy_zero_julia": cfgkey("j", False, True, False),
            "mandy_reset_translation": cfgkey("t", False, False, False),
            "mandy_reset_rotation": cfgkey("r", False, False, False),
            "mandy_reset_zoom": cfgkey("z", False, False, False),
            "mandy_reset": cfgkey("x", False, False, False),
            "mandy_pause": cfgkey("space", False, False, False),
            "mandy_step": cfgkey("s", False, False, False),
            "mandy_next": cfgkey("period", False, False, False),
            "mandy_prev": cfgkey("comma", False, False, False),
        }

        self.mappable_keys = [
            "play",
            "reset",
            "record",
            "multi_record",
            "track_clear",
            "panic",
            "play_mode",
        ]

        self.midi_in = {
            "play": None,
            "multi_record": None,
        }

        self.midi_default_input = ""
        self.midi_default_output = ""

        self.velocity_keys = "zxcvbnm"
        self.piano_white_keys = "zxcvbnmqwertyu"
        self.piano_black_keys = "sdghj23567"
        self.n_backups = 0
        self.autosave_seq = True
        self.autosave_trk = False
        self.ask_quit = False

        self.cfg_parser = self.build_parser()

    def build_parser(self):
        cfg = configparser.ConfigParser()
        cfg["looknfeel"] = {
            "window_opacity": self.window_opacity,
            "seq_font": self.seq_font,
            "console_font": self.console_font,
            "matrix_font": self.mixer_font,
            "timeline_font": self.timeline_font,
            "seq_colour": self.colour,
            "console_colour": self.console_colour,
            "matrix_colour": self.mixer_colour,
            "timeline_colour": self.timeline_colour,
            "mandy_colour": self.mandy_colour,
            "star_colour": self.star_colour,
            "record_colour": self.record_colour,
            "seq_spacing": self.seq_spacing,
            "notebook_mouseover": self.notebook_mouseover,
            "track_prop_mouseover": self.track_prop_mouseover,
            "dark_theme": self.dark_theme,
            "popup_transition": self.popup_transition,
        }

        cfg["advanced"] = {
            "ask_quit": self.ask_quit,
            "quick_controls_desc": self.quick_controls_desc,
            "quick_control_1_ctrl": self.quick_control_1_ctrl,
            "quick_control_1_def": self.quick_control_1_def,
            "quick_control_2_ctrl": self.quick_control_2_ctrl,
            "quick_control_2_def": self.quick_control_2_def,
            "piano_white_keys": self.piano_white_keys,
            "piano_black_keys": self.piano_black_keys,
            "velocity_keys": self.velocity_keys,
        }

        cfg["backup"] = {
            "n_backups": str(self.n_backups),
            "autosave_seq": self.autosave_seq,
            "autosave_trk": self.autosave_trk,
            "last_load_path": self.last_load_path,
            "last_save_path": self.last_save_path,
        }

        cfg["midi"] = {
            "midi_default_input": self.midi_default_input,
            "midi_default_output": self.midi_default_output,
        }

        cfg["midi_map"] = {}

        cfg["render"] = {
            "render_mode": str(self.render_mode),
            "render_secs": str(self.render_secs),
            "render_meter": str(self.render_meter),
            "render_format": self.render_format,
            "render_folder": self.render_folder,
            "render_midi": self.render_midi,
            "render_timecode": str(self.render_timecode),
            "render_ticks": str(self.render_ticks),
        }

        cfg["other"] = {
            "new_tracks_left": self.new_tracks_left,
            "new_seqs_with_tracks": self.new_seqs_with_tracks,
            "port_popup": self.port_popup,
            "pnq_hack": self.pnq_hack,
            "inception": self.inception,
        }

        return cfg

    def save(self):
        lnf = self.cfg_parser["looknfeel"]
        lnf["window_opacity"] = str(self.window_opacity)
        lnf["seq_font"] = self.seq_font
        lnf["console_font"] = self.console_font
        lnf["matrix_font"] = self.mixer_font
        lnf["timeline_font"] = self.timeline_font
        lnf["seq_spacing"] = str(self.seq_spacing)
        lnf["seq_colour"] = str(self.colour)
        lnf["console_colour"] = str(self.console_colour)
        lnf["matrix_colour"] = str(self.mixer_colour)
        lnf["timeline_colour"] = str(self.timeline_colour)
        lnf["mandy_colour"] = str(self.mandy_colour)
        lnf["star_colour"] = str(self.star_colour)
        lnf["record_colour"] = str(self.record_colour)
        lnf["notebook_mouseover"] = str(self.notebook_mouseover)
        lnf["track_prop_mouseover"] = str(self.track_prop_mouseover)
        lnf["dark_theme"] = str(self.dark_theme)
        lnf["timeline_show"] = str(self.timeline_show)
        lnf["popup_transition"] = str(self.popup_transition)

        adv = self.cfg_parser["advanced"]
        adv["ask_quit"] = str(self.ask_quit)
        adv["quick_controls_desc"] = self.quick_controls_desc
        adv["quick_control_1_ctrl"] = str(self.quick_control_1_ctrl)
        adv["quick_control_1_def"] = str(self.quick_control_1_def)
        adv["quick_control_2_ctrl"] = str(self.quick_control_2_ctrl)
        adv["quick_control_2_def"] = str(self.quick_control_2_def)
        adv["piano_white_keys"] = self.piano_white_keys
        adv["piano_black_keys"] = self.piano_black_keys
        adv["velocity_keys"] = self.velocity_keys

        bck = self.cfg_parser["backup"]
        bck["n_backups"] = str(self.n_backups)
        bck["autosave_seq"] = str(self.autosave_seq)
        bck["autosave_trk"] = str(self.autosave_trk)
        bck["last_load_path"] = str(self.last_load_path)
        bck["last_save_path"] = str(self.last_save_path)

        mid = self.cfg_parser["midi"]

        mid["midi_default_input"] = self.midi_default_input
        mid["midi_default_output"] = self.midi_default_output

        mmp = self.cfg_parser["midi_map"]
        mmp.clear()
        for mi, mn in self.midi_in.items():
            if mi:
                mmp[mi] = str(mn) if mn else ""

        rnd = self.cfg_parser["render"]
        rnd["render_mode"] = str(self.render_mode)
        rnd["render_secs"] = str(self.render_secs)
        rnd["render_meter"] = str(self.render_meter)
        rnd["render_format"] = self.render_format
        rnd["render_midi"] = str(self.render_midi)
        rnd["render_folder"] = self.render_folder
        rnd["render_timecode"] = str(self.render_timecode)
        rnd["render_ticks"] = str(self.render_ticks)

        oth = self.cfg_parser["other"]
        oth["new_tracks_left"] = str(self.new_tracks_left)
        oth["new_seqs_with_tracks"] = str(self.new_seqs_with_tracks)
        oth["port_popup"] = str(self.port_popup)
        oth["pnq_hack"] = str(self.pnq_hack)
        oth["inception"] = str(self.inception)

        with open(self.filename, "w") as cfgfile:
            self.cfg_parser.write(cfgfile)

    def load(self, filename):
        self.filename = filename

        if self.cfg_parser.read(filename):
            lnf = self.cfg_parser["looknfeel"]
            self.seq_font = lnf["seq_font"]
            self.window_opacity = float(lnf["window_opacity"])
            self.console_font = lnf["console_font"]
            self.mixer_font = lnf["matrix_font"]
            self.timeline_font = lnf["timeline_font"]
            self.seq_spacing = float(lnf["seq_spacing"])
            self.colour = tuple(
                [float(a.strip(" '")) for a in lnf["seq_colour"].strip("()").split(",")]
            )
            self.console_colour = tuple(
                [
                    float(a.strip(" '"))
                    for a in lnf["console_colour"].strip("()").split(",")
                ]
            )
            self.mixer_colour = tuple(
                [
                    float(a.strip(" '"))
                    for a in lnf["matrix_colour"].strip("()").split(",")
                ]
            )
            self.timeline_colour = tuple(
                [
                    float(a.strip(" '"))
                    for a in lnf["timeline_colour"].strip("()").split(",")
                ]
            )
            self.star_colour = tuple(
                [
                    float(a.strip(" '"))
                    for a in lnf["star_colour"].strip("()").split(",")
                ]
            )
            self.record_colour = tuple(
                [
                    float(a.strip(" '"))
                    for a in lnf["record_colour"].strip("()").split(",")
                ]
            )

            self.mandy_colour = tuple(
                [
                    float(a.strip(" '"))
                    for a in lnf["mandy_colour"].strip("()").split(",")
                ]
            )

            self.notebook_mouseover = lnf.getboolean("notebook_mouseover")
            self.track_prop_mouseover = lnf.getboolean("track_prop_mouseover")
            self.dark_theme = lnf.getboolean("dark_theme")
            self.timeline_show = lnf.getboolean("timeline_show")
            self.popup_transition = lnf.getboolean("popup_transition")
            adv = self.cfg_parser["advanced"]
            self.ask_quit = adv.getboolean("ask_quit")
            self.quick_controls_desc = adv["quick_controls_desc"]
            self.quick_control_1_ctrl = adv.getint("quick_control_1_ctrl")
            self.quick_control_1_def = adv.getint("quick_control_1_def")
            self.quick_control_2_ctrl = adv.getint("quick_control_2_ctrl")
            self.quick_control_2_def = adv.getint("quick_control_2_def")
            self.piano_white_keys = adv["piano_white_keys"]
            self.piano_black_keys = adv["piano_black_keys"]
            self.velocity_keys = adv["velocity_keys"]

            bck = self.cfg_parser["backup"]
            self.n_backups = bck.getint("n_backups")
            self.autosave_seq = bck.getboolean("autosave_seq")
            self.autosave_trk = bck.getboolean("autosave_trk")
            self.last_load_path = bck["last_load_path"]
            self.last_save_path = bck["last_save_path"]

            mid = self.cfg_parser["midi"]

            self.midi_default_input = mid["midi_default_input"]
            self.midi_default_output = mid["midi_default_output"]

            mmp = self.cfg_parser["midi_map"]
            if mmp:
                self.midi_in.clear()

            for m, mm in mmp.items():
                if mm:
                    self.midi_in[m] = tuple(
                        [int(a.strip(" '")) for a in mm.strip("()").split(",")]
                    )
                else:
                    self.midi_in[m] = None

            rnd = self.cfg_parser["render"]

            self.render_mode = rnd.getint("render_mode")
            self.render_secs = rnd.getint("render_secs")
            self.render_meter = rnd.getint("render_meter")
            self.render_format = rnd["render_format"]
            self.render_midi = rnd.getboolean("render_midi")
            self.render_timecode = rnd.getint("render_timecode")
            self.render_ticks = rnd.getint("render_ticks")
            self.render_folder = rnd["render_folder"]

            oth = self.cfg_parser["other"]
            self.new_tracks_left = oth.getboolean("new_tracks_left")
            self.new_seqs_with_tracks = oth.getboolean("new_seqs_with_tracks")
            self.port_popup = oth.getboolean("port_popup")
            self.pnq_hack = oth.getboolean("pnq_hack")
            self.inception = oth.getboolean("inception")


key_aliases = {
    "KP_Add": "keypad +",
    "KP_Subtract": "keypad -",
    "KP_Multiply": "keypad *",
    "KP_Divide": "keypad /",
    "Page_Up": "page up",
    "Page_Down": "page down",
    "backslash": "\\",
}

ignore_modifiers = {"Control_L"}


class cfgkey:
    def __init__(self, key, shift, ctrl, alt):
        self.key = key
        self.shift = shift
        self.ctrl = ctrl
        self.alt = alt

    def matches(self, event):
        key = Gdk.keyval_name(Gdk.keyval_to_lower(event.keyval))

        if key != self.key:
            return False

        # ignore modifiers?
        for k in ignore_modifiers:
            if key == k:
                return True

        shift = False
        ctrl = False
        alt = False

        if event.state & Gdk.ModifierType.SHIFT_MASK:
            shift = True
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            ctrl = True
        if event.state & Gdk.ModifierType.MOD1_MASK:
            alt = True

        if self.shift != shift:
            return False

        if self.ctrl != ctrl:
            return False

        if self.alt != alt:
            return False

        return True

    def to_accel(self):
        ret = ""
        if self.ctrl:
            ret += "<ctrl>"

        if self.shift:
            ret += "<shift>"

        if self.alt:
            ret += "<alt>"

        ret += "%s" % self.key

        return ret

    def __str__(self):
        ret = ""

        if self.ctrl:
            ret = ret + "ctrl "

        if self.shift:
            ret = ret + "shift "

        if self.alt:
            ret = ret + "alt "

        if self.key in key_aliases:
            ret = ret + "[%s]" % key_aliases[self.key]
        else:
            ret = ret + "[%s]" % self.key.lower()
        return ret
