
def muzakize(pms):
	seq = pms.add_sequence(32)
	trk1 = seq.add_track()
	trk2 = seq.add_track()

	trk1.add_column()

	trk1.port = 0;
	trk1.channel = 10;
	
	trk2.port = 0;
	trk2.channel = 10;

	trk1[0][0] = "c3"
	trk1[0][8] = "c3"
	trk1.nrows = 16
	trk1.nsrows = 16
	
	trk1[1][0] = "f#3"
	trk1[1][4] = "f#3"
	trk1[1][8] = "f#3"
	trk1[1][12] = "f#3"
		
	trk2[0][0] = "f#3"
	trk2[0][4] = "f#3"
	trk2[0][8] = "f#3"
	trk2[0][12] = "f#3"
	trk2[0][16] = "f#3"
	
