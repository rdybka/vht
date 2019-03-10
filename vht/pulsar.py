
class Pulsar():
	def __init__(self, freq):
		self._freq = freq

	@property
	def freq(self):
		return self._freq

	@freq.setter
	def freq(self, f):
		self._freq = f

	def intensity(self, pos):
		r = .8 - ((pos % self._freq) / self._freq)
		return max(r, 0.0)

