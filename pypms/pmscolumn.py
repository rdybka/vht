from collections.abc import MutableSequence
from pypms.pmsrow import PMSRow

class PMSColumn(MutableSequence):
	def __init__(self, pms, trk, col):
		self._pms_handle = pms
		self._trk_handle = trk;
		self._col = col
		super()
	
	def __len__(self):
		return 0;

	def __delitem__(self, itm):
		pass

	# returns row info
	def __getitem__(self, itm):
		return PMSRow(self._pms_handle, self._pms_handle.track_get_row_ptr(self._trk_handle, self._col, itm))
		
	def __setitem__(self, itm, val):
		pass

	def insert(self, itm, val):
		pass

