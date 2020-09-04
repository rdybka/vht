# extras.py - Valhalla Tracker
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

from vht import mod, cfg


def fix_extras_new_trk(s, t):
    x = mod[s][t].extras
    if len(x):
        return

    x["track_name"] = ""
    x["track_keep_name"] = False
    x["ctrl_names"] = {}
    x["track_show_notes"] = True
    x["track_show_timeshift"] = False
    x["track_show_pitchwheel"] = False
    x["track_show_controllers"] = False


def get_name(n):
    nm = n
    valid = False
    while not valid:
        valid = True
        for s in mod:
            if s.extras["sequence_name"] == nm:
                nm = nm + "_"
                valid = False
    return nm


def fix_extras_new_seq(s):
    x = mod[s].extras
    if len(x):
        return

    x["mouse_cfg"] = [3, 2, 0]
    x["sequence_name"] = ""

    txt = get_name(cfg.sequence_name_format % (len(mod) - 1))

    x["sequence_name"] = txt
    x["font_size"] = cfg.seq_font_size


def register(mod):
    mod.cb_new_sequence = [fix_extras_new_seq]
    mod.cb_new_track = [fix_extras_new_trk]
