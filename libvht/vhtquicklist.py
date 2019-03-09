from collections.abc import Iterable

# a wrapper for the c int_array
class VHTQuickList(Iterable):
	def __init__(self, i, l):
		self._i = i
		self._l = l;
		super()

	def __len__(self):
		return self._l

	def __iter__(self):
		for itm in range(self._l):
			yield int(self._i[itm])

	def __getitem__(self, itm):
		if itm >= self._l:
			raise IndexError(itm, "no parrots here")

		if itm < 0:
			raise IndexError(itm, "don't be so negative")

		return int(self._i[itm])
