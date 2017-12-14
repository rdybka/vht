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
from libvht import libcvht
from libvht.vhtsequence import VHTSequence

class VHTModule(Iterable):
	# a somewhat pythonic interface to the vht magic
	def __init__(self):
		self._seq = None
		self.active_track = None
		libcvht.module_new();
		super()
	
	def __del__(self):   
		libcvht.module_free();
	
	# this will connect and initialise an empty module
	def jack_start(self, name = None):
		return libcvht.start(name)
	
	# disconnect from jack
	def jack_stop(self):
		libcvht.stop()

	def __str__(self):
		r = {}
		r["bpm"] = self.bpm
		r["playing"] = self.playing
		r["nseq"] = len(self.seq)
		r["nports"] = self.nports
		
		return r.__str__()

	def reset(self):
		libcvht.module_reset()

	def new(self):
		self._seq = None
		libcvht.module_new();

	def __len__(self):
		return libcvht.module_get_nseq()

	def __iter__(self):
		for itm in range(self.__len__()):
			yield PMSSequence(libcvht, libcvht.module_get_seq(itm))
		
	def __getitem__(self, itm):
		if itm >= self.__len__():
			raise IndexError()
			
		if itm < 0:
			raise IndexError()
			
		return VHTSequence(libcvht, libcvht.module_get_seq(itm))
    
	def add_sequence(self, length = -1):
		seq = libcvht.sequence_new(length)
		libcvht.module_add_sequence(seq)
		return VHTSequence(libcvht, seq)
    
	def swap_sequence(self, s1, s2):
		libcvht.module_swap_sequence(s1, s2)

	def del_sequence(self, s = -1):
		libcvht.module_del_sequence(s)
    
	def __str__(self):
		ret = "seq: %d\n" % self.__len__()
		for itm in self:
			ret = ret + "%d : %d\n" % (len(itm), itm.length)
		return ret

	def sneakily_queue_midi_note_on(self, port, chn, note, velocity):
		libcvht.queue_midi_note_on(port, chn, note, velocity)
		
	def sneakily_queue_midi_note_off(self, port, chn, note):
		libcvht.queue_midi_note_off(port, chn, note)
	
	@property
	def jack_error(self):
		return libcvht.get_jack_error()
	
	@property
	def playing(self):
		return libcvht.module_is_playing()
	
	@property
	def play(self):
		return libcvht.module_is_playing()
		
	@property
	def curr_seq(self):
		return libcvht.module_get_curr_seq()
		
	@play.setter
	def play(self, value):
		if value:
			libcvht.module_play(1)
		else:
			libcvht.module_play(0)

	@property
	def dump_notes(self):
		return 0	# we need write-only properties in python :)
		
	@dump_notes.setter
	def dump_notes(self, n):
		libcvht.module_dump_notes(n)

	@property
	def bpm(self):
		return libcvht.module_get_bpm()
	
	@bpm.setter
	def bpm(self, value):
		value = min(max(value, self.min_bpm), self.max_bpm)
		libcvht.module_set_bpm(value)

	@property
	def nports(self):
		return libcvht.module_get_nports()
	
	@property
	def time(self):
		return libcvht.module_get_time()

	@property
	def max_ports(self):
		return libcvht.get_jack_max_ports()

	@property
	def min_bpm(self):
		return 1
		
	@property
	def max_bpm(self):
		return 1000
		
