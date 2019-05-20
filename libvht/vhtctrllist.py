# vhtctrllist.py - Valhalla Tracker (libvht)
#
# Copyright (C) 2019 Remigiusz Dybka - remigiusz.dybka@gmail.com
# @schtixfnord
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from collections.abc import Iterable
from libvht.vhtctrl import VHTCtrl

class VHTCtrlList(Iterable):
	def __init__(self, vht, trk):
		self._vht_handle = vht
		self._trk_handle = trk
		self._ctrls = []
		self._update()
		super()

	def __len__(self):
		return self._vht_handle.track_get_nctrl(self._trk_handle)

	def _update(self):
		self._ctrls = eval(self._vht_handle.track_get_ctrl_nums(self._trk_handle))

	def __iter__(self):
		for i in range(self.__len__()):
			yield VHTCtrl(self._vht_handle, self._trk_handle, i, self._ctrls[i], self._update)

	def __getitem__(self, itm):
		if itm >= self.__len__():
			raise IndexError()

		if itm < 0:
			raise IndexError()

		return VHTCtrl(self._vht_handle, self._trk_handle, itm, self._ctrls[itm], self._update)

	def add(self, ctrlnum):
		self._vht_handle.track_add_ctrl(self._trk_handle, ctrlnum)

	def delete(self, ctrl):
		self._vht_handle.track_del_ctrl(self._trk_handle, ctrl)

	def swap(self, ctrl1, ctrl2):
		self._vht_handle.track_swap_ctrl(self._trk_handle, ctrl1, ctrl2)

	def __str__(self):
		ret = ""
		for r in range(self.__len__()):
			ret = ret + str(self[r])
			ret = ret + "\n"

		return ret
