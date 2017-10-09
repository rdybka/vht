from collections.abc import Iterable
from pypms.pmscolumn import PMSColumn

class PMSTrack(Iterable):
	def __init__(self, pms, trk):
		self._pms_handle = pms
		self._trk_handle = trk;
		super()
	
	def __len__(self):
		return self._pms_handle.track_get_ncols(self._trk_handle)

	def __iter__(self):
		for i in range(self.__len__()):
			yield PMSColumn(self._pms_handle, self._trk_handle, i)

	def clear(self):
		for col in self:
			col.clear()
	
	def __getitem__(self, itm):
		return PMSColumn(self._pms_handle, self._trk_handle, itm)

	def __setitem__(self, itm, val):
		pass

	def insert(self, itm, val):
		pass

	def add_column(self):
		self._pms_handle.track_add_col(self._trk_handle)
		
	def swap_column(self, c1, c2):
		self._pms_handle.track_swap_col(self._trk_handle, c1, c2)

	def del_column(self, c = -1):
		if c == -1:
			self._pms_handle.track_del_col(self._trk_handle, self.__len__() - 1)
		else:
			self._pms_handle.track_del_col(self._trk_handle, c)

	@property
	def port(self):
		return self._pms_handle.track_get_port(self._trk_handle)
		
	@port.setter
	def port(self, value):
		self._pms_handle.track_set_port(self._trk_handle, value)

	@property
	def channel(self):
		return self._pms_handle.track_get_channel(self._trk_handle)
		
	@channel.setter
	def channel(self, value):
		self._pms_handle.track_set_channel(self._trk_handle, value)

	@property
	def nrows(self):
		return self._pms_handle.track_get_nrows(self._trk_handle)
		
	@nrows.setter
	def nrows(self, value):
		self._pms_handle.track_set_nrows(self._trk_handle, value)
	
	@property
	def nsrows(self):
		return self._pms_handle.track_get_nsrows(self._trk_handle)
		
	@nsrows.setter
	def nsrows(self, value):
		self._pms_handle.track_set_nsrows(self._trk_handle, value)
	
	@property
	def playing(self):
		return self._pms_handle.track_get_playing(self._trk_handle)
		
	@property
	def pos(self):
		return self._pms_handle.track_get_pos(self._trk_handle)

	def __str__(self):
		ret = ""
		for r in range(self.nrows):
			ret = ret + ("%02d: " % (r))
			for c in range(len(self)):
				rw = self[c][r]
				ret = ret + "| "
				ret = ret + str(rw) + " " 
				
				if (rw.type == 1):
					ret = ret + ("%03d " % (rw.velocity))
				else:
					ret = ret + "    "
			
			ret = ret + "|"
			ret = ret + "\n"
			
		return ret
