# vhtmodule.py - Valhalla Tracker (libvht)
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
from libvht import libcvht
from libvht.vhtsequence import VHTSequence
from libvht.vhttimeline import VHTTimeline
import pickle

class VHTModule(Iterable):
	# a somewhat pythonic interface to the vht magic
	def __init__(self):
		self.active_track = None
		libcvht.module_new();
		self.extras = {} # will be saved - for stuff like names of tracks
		self.timeline = VHTTimeline(libcvht)
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
		self.timeline = VHTTimeline(libcvht)

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

	def free(self):
		libcvht.module_free();

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

	@property
	def rpb(self):
		return libcvht.module_get_rpb()

	@rpb.setter
	def rpb(self, value):
		if value:
			libcvht.module_set_rpb(min(max(1, value), 32))
			self.timeline.changes[0] = [0, self.bpm, self.rpb, 0]

	@property
	def ctrlpr(self):
		return libcvht.module_get_ctrlpr()

	@ctrlpr.setter
	def ctrlpr(self, value):
		libcvht.module_set_ctrlpr(value)

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
		self.timeline.changes[0] = [0, self.bpm, self.rpb, 0]

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
		return .23

	@property
	def max_bpm(self):
		return 1023

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
		jm["rpb"] = self.rpb
		jm["ctrlpr"] = self.ctrlpr
		jm["extras"] = self.extras
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
				t["ctrlpr"] = trk.ctrlpr
				t["program"] = trk.get_program()
				t["qc"] = trk.get_qc()
				t["loop"] = trk.loop
				t["trg_timeline"] = trk.trg_timeline
				t["trg_letring"] = trk.trg_letring
				t["trg_playmode"] = trk.trg_playmode
				t["trg_quantise"] = trk.trg_quantise
				t["trig"] = [trk.get_trig(0), trk.get_trig(1), trk.get_trig(2)]

				t["ctrl"] = []
				for cn, ctrl in enumerate(trk.ctrl):
					c = {}
					c["ctrlnum"] = ctrl.ctrlnum
					c["rows"] = []
					c["doodles"] = []
					rn = 0
					for r in ctrl:
						if r.velocity > -1:
							rw = {}
							rw["n"] = rn
							rw["velocity"] = r.velocity
							rw["linked"] = r.linked
							rw["smooth"] = r.smooth
							rw["anchor"] = r.anchor
							c["rows"].append(rw)

						rn += 1

					for r in range(trk.nrows):
						dood = trk.get_ctrl_rec(cn, r).as_list()
						empty = True
						for d in dood:
							if d > -1:
								empty = False

						if not empty:
							c["doodles"].append([r, dood])

					t["ctrl"].append(c)

				t["col"] = []
				for col in trk:
					c = []
					rn = 0
					for row in col:
						if row.type > 0:
							r = {}
							r["n"] = rn
							r["type"] = row.type
							r["note"] = row.note
							r["velocity"] = row.velocity
							r["delay"] = row.delay
							c.append(r)

						rn += 1
					t["col"].append(c)

				s["trk"].append(t)
			jm["seq"].append(s)


		with open(filename, 'wb') as f:
			pickle.dump(jm, f)

	def load(self, filename):
		if not isinstance(filename, str):
			filename = filename.get_path()

		with open(filename, 'rb') as f:
			try:
				jm = pickle.load(f)
			except:
				print("Couln't load", filename)
				return False

			p = self.play

			self.reset()
			self.new()
			self.bpm = jm["bpm"]
			self.rpb = jm["rpb"]
			self.ctrlpr = jm["ctrlpr"]

			for seq in jm["seq"]:
				s = self.add_sequence()
				s.length = seq["length"]
				for trk in seq["trk"]:
					t = s.add_track(trk["port"], trk["channel"], trk["nrows"], trk["nsrows"], trk["ctrlpr"])
					t.playing = trk["playing"]
					t.set_bank(trk["program"][0], trk["program"][1])
					t.send_program_change(trk["program"][2])
					t.set_qc1(trk["qc"][0], trk["qc"][1])
					t.set_qc2(trk["qc"][2], trk["qc"][3])

					t.loop = trk["loop"]
					t.trg_timeline = trk["trg_timeline"]
					t.trg_letring = trk["trg_letring"]
					t.trg_playmode = trk["trg_playmode"]
					t.trg_quantise = trk["trg_quantise"]

					t.set_trig(0, trk["trig"][0][0], trk["trig"][0][1], trk["trig"][0][2])
					t.set_trig(1, trk["trig"][1][0], trk["trig"][1][1], trk["trig"][1][2])
					t.set_trig(2, trk["trig"][2][0], trk["trig"][2][1], trk["trig"][2][2])

					nctrl = 0
					for ctrl in trk["ctrl"]:
						if ctrl["ctrlnum"] > -1:
							t.ctrl.add(ctrl["ctrlnum"])

						for rw in ctrl["rows"]:
							r = t.ctrl[nctrl][rw["n"]]
							r.velocity = rw["velocity"]
							r.linked = rw["linked"]
							r.smooth = rw["smooth"]
							r.anchor = rw["anchor"]

							t.ctrl[nctrl].refresh()

						for dood in ctrl["doodles"]:
							rn = dood[0] * t.ctrlpr
							for d in dood[1]:
								t.set_ctrl(nctrl, rn, d)
								rn += 1

						nctrl += 1

					for cc, col in enumerate(trk["col"]):
						if cc == 0:
							c = t[0]
						else:
							c = t.add_column()

						for row in col:
							rr = c[row["n"]]
							rr.type = row["type"]
							rr.note = row["note"]
							rr.velocity = row["velocity"]
							rr.delay = row["delay"]

			self.play = p
			self.extras = jm["extras"]

		return True

