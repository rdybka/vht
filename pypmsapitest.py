#!/usr/bin/env python3

import sys
from pypms import pms

if pms.jack_start():
	sys.exit(-1)

print(pms.seq[0].trk[0][0][1])
print(len(pms.seq[0].trk))

pms.jack_stop()
