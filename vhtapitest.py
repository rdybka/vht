#!/usr/bin/env python3

# Valhalla Tracker
#
# Copyright (C) 2017 Remigiusz Dybka
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
from libvht import vht

if vht.jack_start():
	sys.exit(-1)

seq = vht.add_sequence(8)
trk1 = seq.add_track()
trk2 = seq.add_track()

vht.dump_notes = 1
vht.play = 0

input("dupa")

trk1[0][7]="c5"
print(seq)
seq.length = 4
print(seq)
seq.length = 8
print(seq)

vht.jack_stop()
