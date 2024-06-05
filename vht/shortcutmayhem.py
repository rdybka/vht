# shortcutmayhem.py - vahatraker
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

from vht import *
import vht.extras

import gi
import os

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk


def shrt(grp, ttl, k):
    itm = Gtk.ShortcutsShortcut(title=ttl, accelerator=cfg.key[k].to_accel())
    itm.show()
    grp.add(itm)


shorts = {
    "General": [
        ("Open file", "load"),
        ("Save file", "save"),
        ("Quit", "quit"),
        ("Full screen", "fullscreen"),
        ("Toggle timeline", "toggle_timeline"),
        ("Toggle console", "toggle_console"),
        ("Zoom in", "zoom_in"),
        ("Zoom out", "zoom_out"),
    ],
    "Playback": [
        ("Play/Pause", "play"),
        ("Reset (when paused)", "reset"),
        ("Toggle play mode", "play_mode"),
        ("Toggle transport", "toggle_transport"),
        ("Record current", "record"),
        ("Record all", "multi_record"),
        ("Panic", "panic"),
    ],
    "Beats per minute": [
        ("Up", "bpm_up"),
        ("Down", "bpm_down"),
        ("10 Up", "bpm_10_up"),
        ("10 Down", "bpm_10_down"),
        (".01 Up", "bpm_frac_up"),
        (".01 Down", "bpm_frac_down"),
    ],
    "Rows per beat": [
        ("Up", "rpb_up"),
        ("Down", "rpb_down"),
    ],
    "Octave": [("Up", "octave_up"), ("Down", "octave_down")],
    "Skip": [
        ("Up", "skip_up"),
        ("Down", "skip_down"),
    ],
    "Sequence": [
        ("Add", "sequence_add"),
        ("Double", "sequence_double"),
        ("Halve", "sequence_halve"),
        ("Delete", "sequence_delete"),
        ("Clone", "sequence_clone"),
        ("Next", "sequence_next"),
        ("Previous", "sequence_prev"),
        ("Move left", "sequence_move_left"),
        ("Move right", "sequence_move_right"),
    ],
    "Track": [
        ("Toggle notes", "toggle_notes"),
        ("Toggle time", "toggle_time"),
        ("Toggle pitch", "toggle_pitch"),
        ("Toggle controllers", "toggle_controllers"),
        ("Channel up", "channel_up"),
        ("Channel down", "channel_down"),
        ("Port up", "port_up"),
        ("Port down", "port_down"),
        ("Resend patch", "track_resend_patch"),
    ],
    "Track cont.": [
        ("Add", "track_add"),
        ("Delete", "track_del"),
        ("Clear", "track_clear"),
        ("Clone", "track_clone"),
        ("Expand", "track_expand"),
        ("Shrink", "track_shrink"),
        ("Move left", "track_move_left"),
        ("Move right", "track_move_right"),
        ("Move first", "track_move_first"),
        ("Move last", "track_move_last"),
    ],
    "Editing": [
        ("Note off", "note_off"),
        ("Undo", "undo"),
        ("Select all", "select_all"),
        ("Copy", "copy"),
        ("Cut", "cut"),
        ("Paste", "paste"),
        ("Paste over", "paste_over"),
        ("Pull", "pull"),
        ("Push", "push"),
    ],
    "Modifying selection": [
        ("Velocity up", "velocity_up"),
        ("Velocity down", "velocity_down"),
        ("Velocity 10 up", "velocity_10_up"),
        ("Velocity 10 down", "velocity_10_down"),
        ("Transpose up", "transp_up"),
        ("Transpose down", "transp_down"),
        ("Transpose 12 up", "transp_12_up"),
        ("Transpose 12 down", "transp_12_down"),
    ],
    "Controllers": [
        ("Link", "link"),
        ("Shift up", "ctrl_one_up"),
        ("Shift down", "ctrl_one_down"),
    ],
    "Doodles": [
        ("Copy", "doodle_copy"),
        ("Cut", "doodle_cut"),
        ("Paste", "doodle_paste"),
        ("Delete", "doodle_delete"),
        ("Render", "doodle_render"),
    ],
    "Timeline": [],
    "Strip": [
        ("Replace top", "sequence_replace"),
        ("Double", "strip_double"),
        ("Halve", "strip_halve"),
        ("Loop", "sequence_loop"),
    ],
    "Mandy": [
        ("Active", "mandy_active"),
        ("Show info", "mandy_show_info"),
        ("Show crosshair", "mandy_show_crosshair"),
        ("Julia", "mandy_switch_mode"),
        ("Pick julia", "mandy_pick_julia"),
        ("Pause", "mandy_pause"),
        ("Step", "mandy_step"),
        ("Follow", "mandy_next"),
    ],
    "Mandy cont.": [
        ("Direction", "mandy_direction"),
        ("Reset", "mandy_reset"),
        ("Reset julia", "mandy_zero_julia"),
        ("Reset translation", "mandy_reset_translation"),
        ("Reset rotation", "mandy_reset_rotation"),
        ("Reset zoom", "mandy_reset_zoom"),
    ],
    "Mandy left mouse": [],
    "Mandy middle mouse": [],
    "Mandy scroll": [],
}

customs = {
    "General": [("Mute/Unmute", "F1...F12"), ("Piano", "z...m q...u")],
    "Controllers": [
        ("0-127", "z...m"),
        ("Add node / Snap", "<ctrl>"),
    ],
    "Playback": [("Trigger (keypad)", "KP_0...KP_9")],
    "Timeline": [
        ("Snap", "<alt>"),
        ("Zoom / Add bpm node / Clone", "<ctrl>"),
        ("Shift", "<shift>"),
    ],
    "Mandy left mouse": [
        ("Translate", ""),
        ("Rotate", "<shift>"),
        ("Zoom", "<ctrl>"),
    ],
    "Mandy middle mouse": [
        ("Translate julia", ""),
    ],
    "Mandy scroll": [
        ("Zoom", ""),
        ("Iterations", "<ctrl>"),
        ("Speed", "<shift>"),
    ],
}


class ShortcutMayhem(Gtk.ShortcutsWindow):
    def __init__(self):
        super(ShortcutMayhem, self).__init__()

        sect_main = Gtk.ShortcutsSection()
        sect_main.props.max_height = 10

        for g in shorts:
            gr = Gtk.ShortcutsGroup(title=g)
            for itm in shorts[g]:
                shrt(gr, itm[0], itm[1])

            if g in customs:
                for itm in customs[g]:
                    i = Gtk.ShortcutsShortcut(title=itm[0], accelerator=itm[1])
                    i.show()
                    gr.add(i)

            sect_main.add(gr)
            gr.show()

        # shr = Gtk.ShortcutsShortcut(title = "mute/unmute", accelerator = "F1 F9")
        # shr.show()
        # gr_trk.add(shr)

        sect_main.show()
        self.add(sect_main)
