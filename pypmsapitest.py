#!/usr/bin/env python3

import sys
from pypms import pms

if pms.jack_start():
	sys.exit(-1)

# pms.seq.trk.column.row
pms.seq[0][0][0][0].note = "D3" # "C1" "C-1" "C#1" allowed

trk = pms.seq[0][0]

trk.clear()
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

print(trk)


pms.jack_stop()
