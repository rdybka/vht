from collections.abc import Iterable
from libvht.vhtrow import VHTRow

class VHTColumn(Iterable):
	def __init__(self, vht, trk, col):
		self._vht_handle = vht
		self._trk_handle = trk;
		self._col = col
		super()

	def __len__(self):
		return self._vht_handle.track_get_length(self._trk_handle)

	def clear(self):
		for r in self:
			r.clear()

	def __iter__(self):
		for i in range(self.__len__()):
			yield VHTRow(self._vht_handle, self._vht_handle.track_get_row_ptr(self._trk_handle, self._col, i))

	def __setitem__(self, itm, val):
		self[itm].note = val

	def __getitem__(self, itm):
		if itm >= self.__len__():
			raise IndexError()

		if itm < 0:
			raise IndexError()

		return VHTRow(self._vht_handle, self._vht_handle.track_get_row_ptr(self._trk_handle, self._col, itm))

	def __str__(self):
		ret = ""
		for r in range(self.__len__()):
			ret = ret + str(self[r])
			ret = ret + "\n"

		return ret

