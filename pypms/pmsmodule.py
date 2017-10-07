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
from pypms import libpms
from pypms.pmssequencelist import PMSSequenceList

class PMSModule():
	# a somewhat pythonic interface to the pms magic
	# see pypmsapitest.py for general usage
	def __init__(self):
		self._seq = None
		libpms.module_new();
		pass
	
	def __del__(self):   
		libpms.module_free();
	
	# this will connect and initialise an empty module
	def jack_start(self):
		return libpms.start()
	
	# disconnect from jack
	def jack_stop(self):
		libpms.stop()
		pass

	def __str__(self):
		r = {}
		r["bpm"] = self.bpm
		r["playing"] = self.playing
		r["nseq"] = self.nseq
		
		return r.__str__()

	def reset(self):
		libpms.module_reset()

	@property
	def seq(self):
		if self._seq == None:
			self._seq = PMSSequenceList(libpms)
		
		return self._seq

	@property
	def playing(self):
		return libpms.module_is_playing()
		
	@playing.setter
	def playing(self, value):
		if value:
			libpms.module_play(1)
		else:
			libpms.module_play(0)
			
	@property
	def bpm(self):
		return libpms.module_get_bpm()
	
	@bpm.setter
	def bpm(self, value):
		libpms.module_set_bpm(value)
