from collections.abc import MutableSequence
from pypms.pmssequence import PMSSequence

class PMSSequenceList(MutableSequence):
	def __init__(self, pms):
		self._pms_handle = pms
		super()
	
	def __len__(self):
		return self._pms_handle.module_get_nseq()

	def __delitem__(self, itm):
		pass

	def __getitem__(self, itm):
		return PMSSequence(self._pms_handle.module_get_seq(itm))

	def __setitem__(self, itm, val):
		pass

	def insert(self, itm, val):
		pass
    
	def __str__(self):
		return self.trk.__str__()
