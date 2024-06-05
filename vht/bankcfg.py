# bankcfg.py - vahatraker
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
    mod.bank_path = mod.cfg_path + os.sep + "bank"
    if not os.path.exists(mod.bank_path):
        print("creating", mod.bank_path)
        os.mkdir(mod.bank_path)

    # filter our defaults to copy
    try:
        cfg_names = [
            [int(c[0][0]), c[0][1], c[-1]]
            for c in [
                [c.split(os.sep)[-1].split("-"), c]
                for c in glob.glob(mod.bank_path + os.sep + "*-*")
            ]
        ]
    except ValueError:
        print("""ctrl def filenames must be in "23-name" format""")
        sys.exit(-1)

    def_names = [
        [int(c[0][0]), c[0][1], c[-1]]
        for c in [
            [c.split(os.sep)[-1].split("-"), c]
            for c in glob.glob(mod.data_path + os.sep + "bank" + os.sep + "*-*")
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

        phname = mod.bank_path + os.sep + "%d-%s" % (n[0], n[1])
        print("copying", phname)
        copyfile(n[2], phname)

    # refresh just in case
    bank_names = [
        [int(c[0][0]), c[0][1], c[-1]]
        for c in [
            [c.split(os.sep)[-1].split("-"), c]
            for c in glob.glob(mod.bank_path + os.sep + "*-*")
        ]
    ]

    # sort, load, return
    bank_names = sorted(bank_names, key=lambda p: p[0])
    bank = {}
    for n in bank_names:
        b = []
        if n[1]:
            with open(n[2], "r") as ph:
                wild = [-1, -1, -2]  # -2 = *
                sub = ""
                for l in ph.readlines():
                    l = l.strip()
                    if not l:
                        continue

                    if l[0] == "#":
                        continue

                    if l[0] == "[":
                        sub = l[1:-1]
                        continue

                    l = l.split(":")

                    if len(l) == 3:  # check for wildcard change
                        if "*" in l:
                            for w, v in enumerate(l):
                                wild[w] = int(v) if v != "*" else -2
                            continue

                    patch = wild.copy()

                    for p, v in enumerate([int(l) for l in reversed(l[:-1])]):
                        patch[2 - p] = v

                    patch[2] -= 1
                    b.append([patch, sub, l[-1]])

        bank[n[1]] = b

    return bank
