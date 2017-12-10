from vht import *

class PoorMansPiano():
	def __init__(self, trk):
		self.trk = trk
		self.notes = {122: "c", 115: "c#", 120 : "d", 100 : "d#", 99 : "e", 118 : "f",
					103 : "f#", 98 : "g", 104 : "g#", 110 : "a" , 106 : "a#", 109 : "b"}
		self.notes2 = {113: "c", 50 : "c#", 119 : "d", 51 : "d#", 101 : "e", 114 : "f",
					53 : "f#", 116 : "g", 54 : "g#", 121 : "a", 55 : "a#", 117 : "b"}

		self.mnotes = [122, 115, 120, 100, 99, 118, 103, 98, 104, 110, 106, 109]
		self.mnotes2 = [113, 50, 119, 51, 101, 114, 53, 116, 54, 121, 55, 117]


		self.note_on = None
		self.mnotes.append(self.mnotes)
		self.ringing = []

	def silence(self):
		for n in self.ringing:
			self.ringing.remove(n)
			mod.sneakily_queue_midi_note_off(self.trk.port, self.trk.channel, n)
		
		self.note_on = None

	def key2note(self, key, note_off = False):
		mnt = -23
		if key in self.mnotes:
			mnt = self.mnotes.index(key)
		
		if key in self.mnotes2:
			mnt = self.mnotes2.index(key) + 12
		
		if mnt == -23:
			return None
			
		mnt += cfg.octave * 12
		while mnt > 127:
			mnt -= 12
	
		if not note_off:
			if not self.note_on == mnt:
				mod.sneakily_queue_midi_note_on(self.trk.port, self.trk.channel, mnt, cfg.velocity)
				self.note_on = mnt
				self.ringing.append(mnt)
		else:
			self.note_on = None
			mod.sneakily_queue_midi_note_off(self.trk.port, self.trk.channel, mnt)
			while mnt in self.ringing:
				self.ringing.remove(mnt)
			
		octave = cfg.octave
		if key in self.notes:
			return "%s%d" % (self.notes[key], octave)
		
		octave = cfg.octave
		octave += 1
		if octave > 8:
			octave = 8	
		if key in self.notes2:
			return "%s%d" % (self.notes2[key], octave)
		return None
