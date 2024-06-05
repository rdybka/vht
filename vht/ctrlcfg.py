# ctrlcfg.py - vahatraker
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

import sys
import os
import glob
from shutil import copyfile
from vht import mod, cfg


def load():
    # bad, bad, bad!
    mod.ctrl_path = mod.cfg_path + os.sep + "ctrl"
    if not os.path.exists(mod.ctrl_path):
        print("creating", mod.ctrl_path)
        os.mkdir(mod.ctrl_path)

    # filter our defaults to copy
    try:
        cfg_names = [
            [int(c[0][0]), c[0][1], c[-1]]
            for c in [
                [c.split(os.sep)[-1].split("-"), c]
                for c in glob.glob(mod.ctrl_path + os.sep + "*-*")
            ]
        ]
    except ValueError:
        print("""ctrl def filenames must be in "23-name" format""")
        sys.exit(-1)

    def_names = [
        [int(c[0][0]), c[0][1], c[-1]]
        for c in [
            [c.split(os.sep)[-1].split("-"), c]
            for c in glob.glob(mod.data_path + os.sep + "ctrl" + os.sep + "*-*")
        ]
    ]

    for n in cfg_names:
        for nn in def_names:
            if n[1] == nn[1]:
                def_names.remove(nn)

    # copy them minding the numbers
    for n in def_names:
        rep = True
        while rep:
            rep = not rep
            for nn in cfg_names:
                if n[0] == nn[0]:
                    n[0] += 1
                    rep = True

        phname = mod.ctrl_path + os.sep + "%d-%s" % (n[0], n[1])
        print("copying", phname)
        copyfile(n[2], phname)

    # refresh just in case
    cfg_names = [
        [int(c[0][0]), c[0][1], c[-1]]
        for c in [
            [c.split(os.sep)[-1].split("-"), c]
            for c in glob.glob(mod.ctrl_path + os.sep + "*-*")
        ]
    ]

    # sort, load, return
    cfg_names = sorted(cfg_names, key=lambda p: p[0])
    cfgs = {}
    for n in cfg_names:
        cfg = {}
        if n[1]:
            with open(n[2], "r") as ph:
                for l in ph.readlines():
                    l = l.strip()
                    if not l:
                        continue

                    if l[0] != "#":
                        l = l.split(":")
                        if len(l) == 2:
                            cfg[int(l[0])] = l[1]
                cfgs[n[1]] = cfg

    return cfgs
