#!/usr/bin/env python3

import sys
from pypms import pms

if pms.jack_start():
	sys.exit(-1)

# pms.seq.trk.column.row

# assignment
pms.seq[0][0][0][0] = "D3" # int, "C1" "C-1" "C#1" allowed
pms.seq[0][0][0][0].note = "D3"

trk = pms.seq[0][0]
print(trk)

# dynamic resize
trk.nrows = 10
print(trk)

vel = 100
n = 12
for col in trk:
	for row in col:
		row.velocity = vel
		row.note = "C5"
		row.note = row.note + n
	
		n = n + 1
		vel = vel + 1

# going smaller leaves hidden rows
trk.nrows = 2
print(trk)
trk.nrows = 15

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
