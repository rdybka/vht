# Valhalla Tracker
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
import json

class VHTModule(Iterable):
	# a somewhat pythonic interface to the vht magic
	def __init__(self):
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

		return r.__str__()

	def reset(self):
		libcvht.module_reset()

	def new(self):
		libcvht.module_new();

	def __len__(self):
		return libcvht.module_get_nseq()

	def __iter__(self):
		for itm in range(self.__len__()):
			yield VHTSequence(libcvht, libcvht.module_get_seq(itm))

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

	# sneaky as a dead parrot...
	def sneakily_queue_midi_note_on(self, seq, port, chn, note, velocity):
		libcvht.queue_midi_note_on(seq, port, chn, note, velocity)

	def sneakily_queue_midi_note_off(self, seq, port, chn, note):
		libcvht.queue_midi_note_off(seq, port, chn, note)

	def sneakily_queue_midi_ctrl(self, seq, trk, value, ctrl):
		libcvht.queue_midi_ctrl(seq, trk, value, ctrl)

	@property
	def jack_error(self):
		return libcvht.get_jack_error()

	@property
	def play(self):
		return libcvht.module_is_playing()

	@property
	def record(self):
		return libcvht.module_is_recording()

	@property
	def curr_seq(self):
		return libcvht.module_get_curr_seq()

	@record.setter
	def record(self, value):
		if value:
			libcvht.module_record(value)
		else:
			libcvht.module_record(0)

	@play.setter
	def play(self, value):
		if value:
			libcvht.module_play(1)
		else:
			libcvht.module_play(0)
			self.record = 0

	@property
	def dump_notes(self):
		return 0	# what is this?

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

	# those two work non-realtime,
	# actual recording happens in c
	def clear_midi_in(self):
		libcvht.midi_in_clear_events()

	def get_midi_in_event(self):
		midin = libcvht.midi_in_get_event()
		if midin:
			return eval(midin)
		else:
			return None

	# so we don't record control midi events
	# expects a list of (channel, evt_type, note) tuples
	def set_midi_record_ignore(self, midig):
		libcvht.midi_ignore_buffer_clear()
		for ig in midig:
			libcvht.midi_ignore_buffer_add(ig[0], ig[1], ig[2])

	def set_default_midi_port(self, port):
		libcvht.set_default_midi_port(port)

	def save(self, filename):
		jm = {}
		jm["bpm"] = self.bpm
		jm["seq"] = []
		for seq in self:
			s = {}
			s["length"] = seq.length
			s["trk"] = []

			for trk in seq:
				t = {}
				t["port"] = trk.port
				t["channel"] = trk.channel
				t["nrows"] = trk.nrows
				t["nsrows"] = trk.nsrows
				t["playing"] = trk.playing
				t["col"] = []

				for col in trk:
					c = []
					for row in col:
						r = {}
						r["type"] = row.type
						r["note"] = row.note
						r["velocity"] = row.velocity
						r["delay"] = row.delay
						c.append(r)
					t["col"].append(c)
				s["trk"].append(t)
			jm["seq"].append(s)


		with open(filename, 'w') as f:
			json.dump(jm, f, indent = 4)
			print("saved %s\n" % (filename))

	def load(self, filename):
		with open(filename, 'r') as f:
			jm = json.load(f)
			p = self.play
			self.reset()
			libcvht.module_new();
			self.bpm = jm["bpm"]
			for seq in jm["seq"]:
				s = self.add_sequence()
				s.length = seq["length"]
				for trk in seq["trk"]:
					t = s.add_track(trk["port"], trk["channel"], trk["nrows"], trk["nsrows"])
					t.playing = trk["playing"]
					for cc, col in enumerate(trk["col"]):
						if cc == 0:
							c = t[0]
						else:
							c = t.add_column()

						for r, row in enumerate(col):
							rr = c[r]
							rr.type = row["type"]
							rr.note = row["note"]
							rr.velocity = row["velocity"]
							rr.delay = row["delay"]

			self.play = p
			print("loaded %s\n" % (filename))

