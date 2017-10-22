from pypms import pms

def track_fill(trk, note = "c3", skip = 2, velocity = 100):
	for r in range(len(trk[0])):
		if r % skip == 0:
			trk[0][r] = note
			trk[0][r].velocity = velocity
	
def muzakize():
	seq = pms.add_sequence(32)
	t1 = seq.add_track()
	t2 = seq.add_track()
	
	t1.channel = t2.channel = 10
	
	track_fill(t1, "c3", 8)
	track_fill(t2, "f#3", 4)
	t1.add_column()
	t1.add_column()

#	for i in range(10):
#		t = seq.add_track()
#		t.channel = i + 1
		
#		for r in range(20):
#			t[0][r] = "c3"
#			t[0][r].velocity = 100 + i + 1
