# Poor Man's Sequencer
#
# Copyright (C) 2017 Remigiusz Dybka
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
from pypms import libpms
from pypms.pmssequence import PMSSequence

class PMSModule(Iterable):
	# a somewhat pythonic interface to the pms magic
	# see pypmsapitest.py for general usage
	def __init__(self):
		self._seq = None
		libpms.module_new();
		super()
	
	def __del__(self):   
		libpms.module_free();
	
	# this will connect and initialise an empty module
	def jack_start(self, name = None):
		return libpms.start(name)
	
	# disconnect from jack
	def jack_stop(self):
		libpms.stop()

	def __str__(self):
		r = {}
		r["bpm"] = self.bpm
		r["playing"] = self.playing
		r["nseq"] = len(self.seq)
		r["nports"] = self.nports
		
		return r.__str__()

	def reset(self):
		libpms.module_reset()

	def new(self):
		self._seq = None
		libpms.module_new();

	def __len__(self):
		return self.libpms.module_get_nseq()

	def __iter__(self):
		for itm in range(self.__len__()):
			yield PMSSequence(libpms, libpms.module_get_seq(itm))
		
	def __getitem__(self, itm):
		if itm >= self.__len__():
			raise IndexError()
			
		if itm < 0:
			raise IndexError()
			
		return PMSSequence(libpms, libpms.module_get_seq(itm))
    
	def add_sequence(self, length = -1):
		seq = libpms.sequence_new(length)
		libpms.module_add_sequence(seq)
		return PMSSequence(libpms, seq)
    
	def swap_sequence(self, s1, s2):
		libpms.module_swap_sequence(s1, s2)

	def del_sequence(self, s = -1):
		libpms.module_del_sequence(s)
    
	def __str__(self):
		ret = "seq: %d\n" % self.__len__()
		for itm in self:
			ret = ret + "%d : %d\n" % (len(itm), itm.length)
		return ret

	@property
	def jack_error(self):
		return libpms.get_jack_error()
	
	@property
	def play(self):
		return libpms.module_is_playing()
		
	@play.setter
	def play(self, value):
		if value:
			libpms.module_play(1)
		else:
			libpms.module_play(0)

	@property
	def dump_notes(self):
		return 0	# we need write-only properties in python :)
		
	@dump_notes.setter
	def dump_notes(self, n):
		libpms.module_dump_notes(n)


	@property
	def bpm(self):
		return libpms.module_get_bpm()
	
	@bpm.setter
	def bpm(self, value):
		libpms.module_set_bpm(value)

	@property
	def nports(self):
		return libpms.module_get_nports()
	
	@nports.setter
	def nports(self, value):
		libpms.module_set_nports(value)
