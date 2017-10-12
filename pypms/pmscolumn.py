from collections.abc import Iterable
from pypms.pmsrow import PMSRow

class PMSColumn(Iterable):
	def __init__(self, pms, trk, col):
		self._pms_handle = pms
		self._trk_handle = trk;
		self._col = col
		super()
		
	def __len__(self):
		return self._pms_handle.track_get_length(self._trk_handle)

	def clear(self):
		for r in self:
			r.clear()

	def __iter__(self):
		for i in range(self.__len__()):
			yield PMSRow(self._pms_handle, self._pms_handle.track_get_row_ptr(self._trk_handle, self._col, i))

	def __setitem__(self, itm, val):
		self[itm].note = val

	def __getitem__(self, itm):
		if itm >= self.__len__():
			raise IndexError()
			
		if itm < 0:
			raise IndexError()
			
		return PMSRow(self._pms_handle, self._pms_handle.track_get_row_ptr(self._trk_handle, self._col, itm))
		
	def __str__(self):
		ret = ""
		for r in range(self.__len__()):
			ret = ret + str(self[r])
			ret = ret + "\n"

		return ret
		
