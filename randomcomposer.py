from pypms import pms

def muzakize():
	seq = pms.add_sequence(32)

	for i in range(10):
		t = seq.add_track()
		t.channel = i + 1
		
		for r in range(20):
			t[0][r] = "c3"
			t[0][r].velocity = 100 + i + 1
