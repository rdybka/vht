from vht import *

def track_fill(trk, note = "c3", skip = 2, velocity = 100):
	for r in range(len(trk[0])):
		if r % skip == 0:
			trk[0][r] = note
			trk[0][r].velocity = velocity
	
def muzakize():
	mod.bpm = 123
	
	seq = mod.add_sequence(32)
	t1 = seq.add_track()
	#t1.add_column()
	return
	
	t1 = seq.add_track()
	t2 = seq.add_track()
	t3 = seq.add_track()
	
	t1.channel = t2.channel = 10
	t3.channel = 2
	
	track_fill(t1, "c3", 8)
	track_fill(t2, "f#3", 2)
	track_fill(t3, "d3", 16)
	t1.add_column()
	t1.add_column()
	
	t1[0][8].clear()
	t1[1][8] = "d3"
	
	t1[0][24].clear()
	t1[1][24] = "d3"
	
	t1[0][14] = "c3"
	t1[0][14].velocity = 90
	
	t1[0][22] = "c3"
	t1[0][22].velocity = 90
	
	t1[0][28] = "c3"
	t1[0][28].velocity = 100
	
	
	t2[0][30] = "a#3"
	

#	for i in range(10):
#		t = seq.add_track()
#		t.channel = i + 1
		
#		for r in range(20):
#			t[0][r] = "c3"
#			t[0][r].velocity = 100 + i + 1
