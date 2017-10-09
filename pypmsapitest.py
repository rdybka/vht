#!/usr/bin/env python3

# Poor Man's Sequencer
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
from pypms import pms

if pms.jack_start():
	sys.exit(-1)

# pms.seq.trk.column.row

# assignment
pms.seq[0][0][0][0] = "D3" # int, "C1" "C-1" "C#1" allowed
pms.seq[0][0][0][0].note = "D3"

trk = pms.seq[0][0]

# fill with random data
vel = 100
n = 12
for col in trk:
	for row in col:
		row.velocity = vel
		row.note = "C5"
		row.note = row.note + n
	
		n = n + 1
		vel = vel + 1

print(trk)

# dynamic resize
trk.nrows = 10
print(trk)

# going smaller leaves hidden rows
trk.nrows = 2
print(trk)
trk.nrows = 15
print(trk)

# columns
trk.add_column()
trk.add_column()
print(trk)
trk.swap_column(0, 2)
trk[0][0] = "C5"
trk[1][0] = "D6"
print(trk)
trk.del_column(1)
print(trk)

# delete last column, always leave one
trk.del_column()
trk.del_column()
trk.del_column()
trk.del_column()
trk.del_column()
print(trk)

pms.jack_stop()
