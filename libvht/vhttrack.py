# vhttrack.py - Valhalla Tracker (libvht)
#
# Copyright (C) 2019 Remigiusz Dybka - remigiusz.dybka@gmail.com
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
from libvht.vhtcolumn import VHTColumn
from libvht.vhtctrllist import VHTCtrlList
from libvht.vhtquicklist import VHTQuickList

class VHTTrack(Iterable):
	def __init__(self, vht, trk, index):
		self._vht_handle = vht
		self._trk_handle = trk
		self.index = index
		super()

	def __len__(self):
		return self._vht_handle.track_get_ncols(self._trk_handle)

	def __iter__(self):
		for itm in range(self.__len__()):
			yield VHTColumn(self._vht_handle, self._trk_handle, itm)

	def clear(self):
		for col in self:
			col.clear()

	def __getitem__(self, itm):
		if itm >= self.__len__():
			raise IndexError(itm, "always look on...")

		if itm < 0:
			raise IndexError(itm, "...the bright side of life")

		return VHTColumn(self._vht_handle, self._trk_handle, itm)

	def __setitem__(self, itm, val):
		pass

	def insert(self, itm, val):
		pass

	def add_column(self):
		self._vht_handle.track_add_col(self._trk_handle)
		return self[self.__len__() - 1]

	def swap_column(self, c1, c2):
		self._vht_handle.track_swap_col(self._trk_handle, c1, c2)

	def del_column(self, c = -1):
		if c == -1:
			self._vht_handle.track_del_col(self._trk_handle, self.__len__() - 1)
		else:
			self._vht_handle.track_del_col(self._trk_handle, c)

	def kill_notes(self):
		self._vht_handle.track_kill_notes(self._trk_handle)

	@property
	def port(self):
		return self._vht_handle.track_get_port(self._trk_handle)

	@port.setter
	def port(self, value):
		self.kill_notes()
		self._vht_handle.track_set_port(self._trk_handle, value)

	@property
	def channel(self):
		return self._vht_handle.track_get_channel(self._trk_handle)

	@channel.setter
	def channel(self, value):
		self.kill_notes()
		self._vht_handle.track_set_channel(self._trk_handle, value)

	@property
	def nrows(self):
		return self._vht_handle.track_get_nrows(self._trk_handle)

	@nrows.setter
	def nrows(self, value):
		self._vht_handle.track_set_nrows(self._trk_handle, value)

	@property
	def nsrows(self):
		return self._vht_handle.track_get_nsrows(self._trk_handle)

	@nsrows.setter
	def nsrows(self, value):
		self._vht_handle.track_set_nsrows(self._trk_handle, value)

	@property
	def playing(self):
		return self._vht_handle.track_get_playing(self._trk_handle)

	@playing.setter
	def playing(self, value):
		self._vht_handle.track_set_playing(self._trk_handle, value)

	@property
	def pos(self):
		return self._vht_handle.track_get_pos(self._trk_handle)

	@property
	def ctrl(self):
		return VHTCtrlList(self._vht_handle, self._trk_handle)

	# number of controllers / envelopes
	@property
	def nctrl(self):
		return self._vht_handle.track_get_nctrl(self._trk_handle)

	# controller rows per row
	@property
	def ctrlpr(self):
		return self._vht_handle.track_get_ctrlpr(self._trk_handle)

	# controller numbers
	@property
	def ctrls(self):
		return eval(self._vht_handle.track_get_ctrl_nums(self._trk_handle))

	@property
	def loop(self):
		return self._vht_handle.track_get_loop(self._trk_handle)

	@loop.setter
	def loop(self, value):
		self._vht_handle.track_set_loop(self._trk_handle, value)

	@property
	def trg_timeline(self):
		return self._vht_handle.track_get_trg_timeline(self._trk_handle)

	@trg_timeline.setter
	def trg_timeline(self, value):
		self._vht_handle.track_set_trg_timeline(self._trk_handle, value)

	@property
	def trg_letring(self):
		return self._vht_handle.track_get_trg_letring(self._trk_handle)

	@trg_letring.setter
	def trg_letring(self, value):
		self._vht_handle.track_set_trg_letring(self._trk_handle, value)

	@property
	def trg_playmode(self):
		return self._vht_handle.track_get_trg_playmode(self._trk_handle)

	@trg_playmode.setter
	def trg_playmode(self, value):
		self._vht_handle.track_set_trg_playmode(self._trk_handle, value)

	@property
	def trg_quantise(self):
		return self._vht_handle.track_get_trg_quantise(self._trk_handle)

	@trg_quantise.setter
	def trg_quantise(self, value):
		self._vht_handle.track_set_trg_quantise(self._trk_handle, value)

	def get_trig(self, t):
		return eval(self._vht_handle.track_get_trig(self._trk_handle, t))

	def set_trig(self, t, tp, ch, nt):
		self._vht_handle.track_set_trig(self._trk_handle, t, tp, ch, nt)

	def send_program_change(self, prog):
		self._vht_handle.track_set_program(self._trk_handle, prog)

	def set_qc1(self, ctrl, val):
		self._vht_handle.track_set_qc1(self._trk_handle, ctrl, val)

	def set_qc2(self, ctrl, val):
		self._vht_handle.track_set_qc2(self._trk_handle, ctrl, val)

	def set_bank(self, msb, lsb):
		self._vht_handle.track_set_bank(self._trk_handle, msb, lsb)

	def get_program(self):
		return eval(self._vht_handle.track_get_program(self._trk_handle))

	def get_qc(self):
		return eval(self._vht_handle.track_get_qc(self._trk_handle))

	# sets control, r = row * ctrlpr + offset
	def set_ctrl(self, c, r, val):
		return self._vht_handle.track_set_ctrl(self._trk_handle, c, r, val)

	# gets all controls for given row (as they will be played)
	def get_ctrl(self, c, r):
		lpr = self.ctrlpr
		ret_arr = self._vht_handle.int_array(lpr)
		self._vht_handle.track_get_ctrl(self._trk_handle, ret_arr, lpr, c, r)

		return VHTQuickList(ret_arr, lpr)

	# gets all controls for given row (recorded/rendered part/doodles)
	def get_ctrl_rec(self, c, r):
		lpr = self.ctrlpr
		ret_arr = self._vht_handle.int_array(lpr)
		self._vht_handle.track_get_ctrl_rec(self._trk_handle, ret_arr, lpr, c, r)

		return VHTQuickList(ret_arr, lpr)

	# gets all controls for given row (env part)
	def get_ctrl_env(self, c, r):
		lpr = self.ctrlpr
		ret_arr = self._vht_handle.int_array(lpr)
		self._vht_handle.track_get_ctrl_env(self._trk_handle, ret_arr, lpr, c, r)

		return VHTQuickList(ret_arr, lpr)

	# gets last sent controller value
	def get_lctrlval(self, c):
		return self._vht_handle.track_get_lctrlval(self._trk_handle, c)

	# get envelope for ctrl c
	def env(self, c):
		return eval(self._vht_handle.track_get_envelope(self._trk_handle, c))

	def env_del_node(self, c, n):
		self._vht_handle.track_envelope_del_node(self._trk_handle, c, n)

	def env_add_node(self, c, x, y, z, linked):
		self._vht_handle.track_envelope_add_node(self._trk_handle, c, x, y, z, linked)

	def env_set_node(self, c, n, x, y, z, linked = -1):
		self._vht_handle.track_envelope_set_node(self._trk_handle, c, n, x, y, z, linked)

	def get_envelope(self, c):
		return eval(self._vht_handle.track_get_envelope(self._trk_handle, c))

	def trigger(self):
		self._vht_handle.track_trigger(self._trk_handle)

	def __str__(self):
		ret = ""
		for r in range(self.nrows):
			ret = ret + ("%02d: " % (r))
			for c, rw in enumerate(self):
				rw = self[c][r]
				ret = ret + "| "
				ret = ret + str(rw) + " "

				if rw.type == 1:
					ret = ret + ("%03d " % (rw.velocity))
				else:
					ret = ret + "    "

			ret = ret + "|"
			ret = ret + "\n"

		return ret

	def clear_updates(self):
		self._vht_handle.track_clear_updates(self._trk_handle)

	def get_rec_update(self):
		rec = self._vht_handle.track_get_rec_update(self._trk_handle)
		if rec:
			return eval(rec)
			
		return None
