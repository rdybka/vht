from vht import *

def track_fill(trk, note = "c3", skip = 2, velocity = 100):
	for r in range(len(trk[0])):
		if r % skip == 0:
			trk[0][r] = note
			trk[0][r].velocity = velocity
	
def muzakize():
	mod.bpm = 123
	
	seq = mod.add_sequence(32)
	seq.add_track()

