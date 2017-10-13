from collections.abc import Iterable
from pypms.pmstrack import PMSTrack

class PMSSequence(Iterable):
	def __init__(self, pms, seq):
		self._pms_handle = pms
		self._seq_handle = seq;
		super()
	
	def __len__(self):
		return self._pms_handle.sequence_get_ntrk(self._seq_handle)

	def __iter__(self):
		for itm in range(self.__len__()):
			yield PMSTrack(self._pms_handle, self._pms_handle.sequence_get_trk(self._seq_handle, itm))
			
	def __getitem__(self, itm):
		if itm >= self.__len__():
			raise IndexError()
			
		if itm < 0:
			raise IndexError()
			
		return PMSTrack(self._pms_handle, self._pms_handle.sequence_get_trk(self._seq_handle, itm))

	def add_track(self, port = 0, channel = 1, length = -1, songlength = -1):
		if length == -1:
			length = self.length
			
		trk = self._pms_handle.track_new(port, channel, length, songlength)
		self._pms_handle.sequence_add_track(self._seq_handle, trk)
		return self[self.__len__() - 1]
		
	def swap_track(self, t1, t2):
		self._pms_handle.sequence_swap_track(self._seq_handle, t1, t2)

	def del_track(self, t = -1):
		self._pms_handle.sequence_del_track(self._seq_handle, t)

	@property
	def length(self):
		return self._pms_handle.sequence_get_length(self._seq_handle)

	@length.setter
	def length(self, value):
		self._pms_handle.sequence_set_length(self._seq_handle, value)



	def __str__(self):
		ret = ""
		for itm in self:
			ret = ret + itm.__str__()
			ret = ret + "\n"
			
		return ret
