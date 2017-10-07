from collections.abc import MutableSequence
from pypms.pmstrack import PMSTrack

class PMSTrackList(MutableSequence):
	def __init__(self, pms, seq):
		self._pms_handle = pms
		self._seq_handle = seq;
		super()
	
	def __len__(self):
		return self._pms_handle.sequence_get_ntrk(self._seq_handle)

	def __delitem__(self, itm):
		pass

	def __getitem__(self, itm):
		return PMSTrack(self._pms_handle, self._pms_handle.sequence_get_trk(self._seq_handle, itm))

	def __setitem__(self, itm, val):
		pass

	def insert(self, itm, val):
		pass
    
	def __str__(self):
		return self.trk.__str__()
