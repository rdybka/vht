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
    mod.extras[s][t] = {}
    mod.extras[s][t]["track_name"] = ""
    mod.extras[s][t]["ctrl_names"] = {}
    mod.extras[s][t]["track_show_notes"] = True
    mod.extras[s][t]["track_show_timeshift"] = False
    mod.extras[s][t]["track_show_pitchwheel"] = False
    mod.extras[s][t]["track_show_controllers"] = False


def fix_extras_new_seq(s):
    mod.extras[s] = {}
    mod.extras[s][-1] = {}

    mod.extras[s][-1]["highlight"] = cfg.highlight
    mod.extras[s][-1]["mouse_cfg"] = [3, 2, 0]
    txt = cfg.sequence_name_format % (len(mod) - 1)

    for rr in mod.extras.values():
        if "sequence_name" in rr[-1]:
            if rr[-1]["sequence_name"] == txt:
                txt = txt + "_"

    mod.extras[s][-1]["sequence_name"] = txt


def fix_extras_post_load(m):
    x = m["extras"]
    for s in x:
        for t in x[s]:
            mod.extras[s][t] = {**mod.extras[s][t], **x[s][t]}


def register(mod):
    mod.cb_new_sequence = [fix_extras_new_seq]
    mod.cb_new_track = [fix_extras_new_trk]
    mod.cb_post_load = [fix_extras_post_load]
