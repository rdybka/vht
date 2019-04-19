from collections.abc import Iterable
from libvht.vhttrack import VHTTrack

class VHTSequence(Iterable):
	def __init__(self, vht, seq):
		self._vht_handle = vht
		self._seq_handle = seq;
		super()

	def __len__(self):
		return self._vht_handle.sequence_get_ntrk(self._seq_handle)

	def __iter__(self):
		for itm in range(self.__len__()):
			yield VHTTrack(self._vht_handle, self._vht_handle.sequence_get_trk(self._seq_handle, itm), itm)

	def __getitem__(self, itm):
		if itm >= self.__len__():
			raise IndexError()

		if itm == -1:
			if not len(self):
				raise IndexError()

			return VHTTrack(self._vht_handle, self._vht_handle.sequence_get_trk(self._seq_handle, self.__len__() - 1), self.__len__() - 1)

		return VHTTrack(self._vht_handle, self._vht_handle.sequence_get_trk(self._seq_handle, itm), itm)

	def add_track(self, port = 0, channel = 1, length = -1, songlength = -1):
		if length == -1:
			length = self.length

		trk = self._vht_handle.track_new(port, channel, length, songlength)
		self._vht_handle.sequence_add_track(self._seq_handle, trk)
		return self[self.__len__() - 1]

	def clone_track(self, trk):
		ntrk = self._vht_handle.sequence_clone_track(self._seq_handle, trk._trk_handle)
		itm = None
		self._vht_handle.track_set_playing(ntrk, 0)
		for t, tt in enumerate (self):
			if tt._trk_handle == ntrk:
				itm = t

		return VHTTrack(self._vht_handle, ntrk, itm) if itm else None

	def double(self):
		self._vht_handle.sequence_double(self._seq_handle)

	def halve(self):
		self._vht_handle.sequence_halve(self._seq_handle)

	def swap_track(self, t1, t2):
		self._vht_handle.sequence_swap_track(self._seq_handle, t1, t2)

	def del_track(self, t = -1):
		if t >= 0:
			self[t].kill_notes()

		self._vht_handle.sequence_del_track(self._seq_handle, t)


	def set_midi_focus(self, foc):
		self._vht_handle.sequence_set_midi_focus(self._seq_handle, foc)

	@property
	def pos(self):
		return self._vht_handle.sequence_get_pos(self._seq_handle)

	@property
	def length(self):
		return self._vht_handle.sequence_get_length(self._seq_handle)

	@length.setter
	def length(self, value):
		self._vht_handle.sequence_set_length(self._seq_handle, value)

	@property
	def max_length(self):
		return self._vht_handle.sequence_get_max_length()

	def __str__(self):
		ret = ""
		for itm in self:
			ret = ret + itm.__str__()
			ret = ret + "\n"

		return ret
