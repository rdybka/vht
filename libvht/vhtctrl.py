from collections.abc import Iterable
from libvht.vhtctrlrow import VHTCtrlRow

class VHTCtrl(Iterable):
	def __init__(self, vht, trk, ctrl, ctrlnum, on_change = None):
		self._vht_handle = vht
		self._trk_handle = trk
		self._ctrl = ctrl
		self._ctrlnum = ctrlnum
		self.on_change = on_change
		super()

	def __len__(self):
		return self._vht_handle.track_get_length(self._trk_handle)

	def clear(self):
		for r in self:
			r.clear()

	def __iter__(self):
		for i in range(self.__len__()):
			yield VHTCtrlRow(self._vht_handle, self._vht_handle.track_get_ctrlrow_ptr(self._trk_handle, self._ctrl, i))

	def __setitem__(self, itm, val):
		self[itm].velocity = val[0]
		self[itm].linked = val[1]
		self[itm].smooth = val[2]
		self[itm].anchor = val[3]

	def __getitem__(self, itm):
		if itm >= self.__len__():
			raise IndexError()

		if itm < 0:
			raise IndexError()

		return VHTCtrlRow(self._vht_handle, self._vht_handle.track_get_ctrlrow_ptr(self._trk_handle, self._ctrl, itm))

	def refresh(self):
		self._vht_handle.track_ctrl_refresh_envelope(self._trk_handle, self._ctrl)

	@property
	def ctrlnum(self):
		return self._ctrlnum

	@ctrlnum.setter
	def ctrlnum(self, value):
		if self._ctrlnum == -1:
			return

		self._ctrlnum = int(value)
		self._vht_handle.track_set_ctrl_num(self._trk_handle, self._ctrl, self._ctrlnum)
		if self.on_change:
			self.on_change()

	def __str__(self):
		ret = "ctrl %d:\n" % self._ctrlnum
		for r in range(self.__len__()):
			ret = ret + str(self[r])
			ret = ret + "\n"

		return ret

	def swap(self, c1, c2):
		self._vht_handle.track_swap_ctrl(self._trk_handle, c1, c2)
