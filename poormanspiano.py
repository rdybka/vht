
from pypms import pms

class PoorMansPiano():
	def __init__(self):
		self.notes = {122: "c", 115: "c#", 120 : "d", 100 : "d#", 99 : "e", 118 : "f",
					103 : "f#", 98 : "g", 104 : "g#", 110 : "a" , 106 : "a#", 109 : "b"}
		self.notes2 = {113: "c", 50 : "c#", 119 : "d", 51 : "d#", 101 : "e", 114 : "f",
					53 : "f#", 116 : "g", 54 : "g#", 121 : "a", 55 : "a#", 117 : "b"}
			
	def key2note(self, key):
		octave = pms.cfg.octave
		if key in self.notes:
			return "%s%d" % (self.notes[key], octave)
		
		octave = pms.cfg.octave
		octave += 1
		if octave > 8:
			octave = 8	
		if key in self.notes2:
			return "%s%d" % (self.notes2[key], octave)
		return None
