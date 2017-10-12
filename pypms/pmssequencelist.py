from collections.abc import Iterable
from pypms.pmssequence import PMSSequence

class PMSSequenceList(Iterable):
	def __init__(self, pms):
		self._pms_handle = pms
		super()
	
	def __len__(self):
		return self._pms_handle.module_get_nseq()

	def __iter__(self):
		for itm in range(self.__len__()):
			yield PMSSequence(self._pms_handle, self._pms_handle.module_get_seq(itm))
		
	def __getitem__(self, itm):
		if itm >= self.__len__():
			raise IndexError()
			
		if itm < 0:
			raise IndexError()
			
		return PMSSequence(self._pms_handle, self._pms_handle.module_get_seq(itm))
    
	def add_sequence(self, length = -1):
		seq = self._pms_handle.sequence_new(length)
		self._pms_handle.module_add_sequence(seq)
		
	def swap_sequence(self, s1, s2):
		self._pms_handle.module_swap_sequence(s1, s2)

	def del_sequence(self, s = -1):
		self._pms_handle.module_del_sequence(s)
    
	def __str__(self):
		ret = "seq: %d\n" % self.__len__()
		for itm in self:
			ret = ret + "%d : %d\n" % (len(itm), itm.length)
		return ret
