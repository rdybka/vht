from collections.abc import MutableSequence
from pypms.pmscolumn import PMSColumn

class PMSTrack(MutableSequence):
	def __init__(self, pms, trk):
		self._pms_handle = pms
		self._trk_handle = trk;
		super()
	
	def __len__(self):
		return self._pms_handle.sequence_get_ntrk(self._seq_handle)

	def __delitem__(self, itm):
		pass

	# returns column
	def __getitem__(self, itm):
		return PMSColumn(self._pms_handle, self._trk_handle, itm)

	def __setitem__(self, itm, val):
		pass

	def insert(self, itm, val):
		pass
