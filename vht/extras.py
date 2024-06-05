# extras.py - vahatraker
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

from vht import mod, cfg


def fix_extras_new_trk(s, t):
    x = mod[s][t].extras
    xx = {}
    xx["track_name"] = ""
    xx["track_keep_name"] = False
    xx["ctrl_names"] = {}
    xx["track_show_notes"] = True
    xx["track_show_timeshift"] = False
    xx["track_show_pitchwheel"] = False
    xx["track_show_controllers"] = False
    xx["track_show_probs"] = False

    for k, v in xx.items():
        if k not in x:
            x[k] = v


def get_name(n):
    nm = n
    valid = False
    while not valid:
        valid = True
        for s in [s for s in mod if "sequence_name" in s.extras]:
            if s.extras["sequence_name"] == nm:
                nm = nm + "_"
                valid = False
    return nm


def fix_extras_new_seq(s):
    x = mod[s].extras
    xx = {}

    xx["mouse_cfg"] = [3, 2, 0]
    xx["font_size"] = cfg.seq_font_size
    xx["sequence_name"] = ""

    if type(s) is int:
        txt = get_name(cfg.sequence_name_format % s)
        xx["sequence_name"] = txt

    for k, v in xx.items():
        if k not in x:
            x[k] = v


def register(mod):
    mod.cb_new_sequence = [fix_extras_new_seq]
    mod.cb_new_track = [fix_extras_new_trk]
