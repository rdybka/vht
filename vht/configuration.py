# configuration.py - Valhalla Tracker
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


import gi

gi.require_version("Gdk", "3.0")
from gi.repository import Gdk


class Configuration:
    def __init__(self):
        self.seq_font = "Monospace"
        self.console_font = "Monospace"
        self.mixer_font = "Monospace"

        # just a default - seq's will have their own (saved in mod.extras)
        self.highlight = 4

        self.seq_font_size = 16
        self.mixer_font_size = 16
        self.mixer_padding = 1.5
        self.seq_line_width = 1.0
        self.seq_spacing = 1.05
        self.status_bar_font_size = 24

        self.console_scale = 1
        self.timeline_position = 0.75
        self.console_position = 0.7
        self.console_show = False
        self.timeline_show = True
        self.console_steal_stderr = True

        c = (0.2, 0.7, 1.0)
        self.colour = c

        c = (0, 0.7, 0.7)
        self.mixer_colour = c

        self.star_colour = (1, 1, 0)
        self.console_colour = self.star_colour
        self.record_colour = (1.0, 0, 0)

        self.popup_timeout = 0.7

        self.intensity_background = 0.2
        self.intensity_txt = 1
        self.intensity_txt_highlight = 3
        self.intensity_lines = 0.6
        self.even_highlight = 1.4
        self.intensity_select = 0.7
        self.pointer_opacity = 0.9
        self.pointer_width = 5
        self.auto_scroll_delay = 0.2
        self.tooltip_markup = """<span font_family="Monospace" size="large">%s</span>"""
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
        self.default_midi_out_port = 0

        self.select_button = 1
        self.delete_button = 3

        self.default_ctrl_name = "zyn"
        self.dark_theme = True
        self.notebook_mouseover = False

        self.quick_controls_desc = "vol/pan:"
        self.quick_control_1_ctrl = 7
        self.quick_control_1_def = 100
        self.quick_control_2_ctrl = 10
        self.quick_control_2_def = 64

        self.new_tracks_left = False
        self.default_seq_length = 16

        self.controller_resolution = 8

        self.last_load_path = ""
        self.last_save_path = ""
        self.save_indication_time = 0.23

        self.key = {
            # sequenceview		shift, ctrl, alt
            "quit": cfgkey("q", False, True, False),
            "toggle_timeline": cfgkey("Tab", False, True, False),
            "toggle_console": cfgkey("grave", False, False, False),
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
            "highlight_up": cfgkey("KP_Multiply", True, False, False),
            "highlight_down": cfgkey("KP_Divide", True, False, False),
            "def_port_up": cfgkey("KP_Multiply", True, True, False),
            "def_port_down": cfgkey("KP_Divide", True, True, False),
            "follow": cfgkey("f", False, False, False),
            "panic": cfgkey("p", False, True, True),
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
            "sequence_add": cfgkey("n", False, True, False),
            "sequence_play_mode": cfgkey("", False, False, False),
            "sequence_next": cfgkey("period", False, True, False),
            "sequence_prev": cfgkey("comma", False, True, False),
            "sequence_move_right": cfgkey("greater", True, True, False),
            "sequence_move_left": cfgkey("less", True, True, False),
            "sequence_double": cfgkey("y", False, True, False),
            "sequence_halve": cfgkey("u", False, True, False),
            "sequence_delete": cfgkey("d", True, True, False),
            "sequence_clone": cfgkey("l", True, True, False),
            "select_all": cfgkey("a", False, True, False),
            "copy": cfgkey("c", False, True, False),
            "cut": cfgkey("x", False, True, False),
            "paste": cfgkey("v", False, True, False),
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
            "port_up": cfgkey("none", True, False, True),
            "port_down": cfgkey("none", True, False, True),
            "hold_editor": cfgkey("Control_L", False, False, False),
            "node_snap": cfgkey("Control_L", False, False, False),
            "toggle_notes": cfgkey("1", False, True, False),
            "toggle_time": cfgkey("2", False, True, False),
            "toggle_pitch": cfgkey("3", False, True, False),
            "toggle_controls": cfgkey("4", False, True, False),
            # controllereditor
            "link": cfgkey("l", False, False, False),
            "doodle_copy": cfgkey("c", True, True, False),
            "doodle_cut": cfgkey("x", True, True, False),
            "doodle_paste": cfgkey("v", True, True, False),
            "doodle_delete": cfgkey("Delete", True, True, False),
            "doodle_render": cfgkey("d", True, True, False),
        }

        self.midi_in = {
            "play": [16, 4, 117, 127],
            "multi_record": [16, 4, 118, 127],
            "reset": [16, 4, 116, 127],
            "track_clear": [16, 4, 113, 127],
        }

        self.velocity_keys = "zxcvbnm"
        self.piano_white_keys = "zxcvbnmqwertyu"
        self.piano_black_keys = "sdghj23567"


key_aliases = {
    "KP_Add": "keypad +",
    "KP_Subtract": "keypad -",
    "KP_Multiply": "keypad *",
    "KP_Divide": "keypad /",
    "Page_Up": "page up",
    "Page_Down": "page down",
    "backslash": "\\",
}

ignore_modifiers = {
    "Control_L",
}


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
