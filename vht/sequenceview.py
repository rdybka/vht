# sequenceview.py - Valhalla Tracker
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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio, GObject
import cairo

from vht import *
from vht.trackview import TrackView
from vht.propview import PropView
from vht.trackpropview import TrackPropView

class SequenceView(Gtk.Box):
	def __init__(self, seq):
		super(SequenceView, self).__init__()

		self._sv = Gtk.ScrolledWindow()
		self._sv.set_events(Gdk.EventMask.POINTER_MOTION_MASK |
			Gdk.EventMask.BUTTON_PRESS_MASK |
			Gdk.EventMask.SCROLL_MASK |
			Gdk.EventMask.ENTER_NOTIFY_MASK |
			Gdk.EventMask.KEY_PRESS_MASK |
			Gdk.EventMask.KEY_RELEASE_MASK)

		cfg.on_highlight.append(self.redraw_track)

		self._sv.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

		self._sv.connect("draw", self.on_draw)
		self._sv.connect("motion-notify-event", self.on_motion)
		self._sv.connect("scroll-event", self.on_scroll)
		self._sv.connect("key-press-event", self.on_key_press)
		self._sv.connect("key-release-event", self.on_key_release)
		self._sv.connect("enter-notify-event", self.on_enter)
		self._sv.connect("button-press-event", self.on_button_press)

		self._sv.set_can_focus(True)

		mod.gui_midi_capture = False
		self.add_tick_callback(self.tick)

		self.seq = seq;

		self.last_count = len(seq)

		self.def_new_track_width = 0

		self._track_box = Gtk.Box()
		self._track_box.set_spacing(0)

		self._sv.add(self._track_box)

		self._side = Gtk.ScrolledWindow()
		self._side.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.EXTERNAL)

		self._side_box = Gtk.Box()
		self._side_box.set_spacing(0)

		self._side.set_events(Gdk.EventMask.POINTER_MOTION_MASK |
			Gdk.EventMask.SCROLL_MASK |
			Gdk.EventMask.ENTER_NOTIFY_MASK |
			Gdk.EventMask.KEY_PRESS_MASK |
			Gdk.EventMask.KEY_RELEASE_MASK)

		self._side.connect("scroll-event", self.on_scroll)
		self._side.connect("key-press-event", self.on_key_press)

		self._side.add_with_viewport(self._side_box)

		self.set_orientation(Gtk.Orientation.VERTICAL)

		hbox = Gtk.Box()
		self.prop_view = PropView(self)
		hbox.pack_end(self.prop_view, True, True, 0)

		self._side_prop = TrackPropView(None, None, self.seq, self, None)
		hbox.pack_start(self._side_prop, False, True, 0)

		self.pack_start(hbox, False, True, 0)

		vbox = Gtk.Box()
		vbox.set_orientation(Gtk.Orientation.VERTICAL)

		hbox = Gtk.Box()
		hbox.pack_start(self._side, False, True, 0)
		hbox.pack_end(self._sv, True, True, 0)

		vbox.pack_start(hbox, True, True, 0)

		self.pack_end(vbox, True, True, 0)

		self._sv_vadj = self._sv.get_vadjustment()
		self._sv_hadj = self._sv.get_hadjustment()

		self._side_vadj = self._side.get_vadjustment()
		self.prop_view_hadj = self.prop_view.get_hadjustment()

		self._sv_vadj.connect("value-changed", self.on_sv_vadj_changed)
		self._side_vadj.connect("value-changed", self.on_sv_vadj_changed)

		self._sv_hadj.connect("value-changed", self.on_sv_hadj_changed)
		self.prop_view_hadj.connect("value-changed", self.on_sv_hadj_changed)

		self.autoscroll_req = False
		self.last_autoscroll_r = -1

		self.build()

		self.show_all()

	def on_button_press(self, widget, event):
		if event.button == cfg.delete_button:
			TrackView.leave_all()
			mod.record = 0

	def on_sv_vadj_changed(self, adj):
		dest_adj = None
		if adj is self._sv_vadj:
			dest_adj = self._side_vadj
		else:
			dest_adj = self._sv_vadj

		dest_adj.set_upper(adj.get_upper())
		dest_adj.set_value(adj.get_value())

	def on_sv_hadj_changed(self, adj):
		dest_adj = None
		if adj is self._sv_hadj:
			dest_adj = self.prop_view_hadj
		else:
			dest_adj = self._sv_hadj

		dest_adj.set_upper(adj.get_upper())
		dest_adj.set_value(adj.get_value())

	def on_key_press(self, widget, event):
		#print(Gdk.keyval_name(Gdk.keyval_to_lower(event.keyval)), event.keyval)
		if cfg.key["play"].matches(event):
			# play/stop
			if mod.play:
				mod.play = 0
				self.prop_view.redraw()
			else:
				mod.play = 1

		if cfg.key["multi_record"].matches(event):
			if mod.record == 2:
				mod.record = 0
				self.prop_view.redraw()
				for trk in self.get_tracks():
					trk.undo_buff.add_state()
					trk.optimise()
				return

			mod.record = 2
			self.prop_view.redraw()
			for trk in self.get_tracks():
				trk.undo_buff.add_state()

			if mod.active_track:
				self.redraw_track(mod.active_track.trk)

			return True

		if cfg.key["record"].matches(event):
			# play/stop
			if mod.record:
				mod.record = 0
				self.prop_view.redraw()
				for trk in self.get_tracks():
					trk.undo_buff.add_state()
					trk.optimise()
			else:
				mod.record = 1
				self.prop_view.redraw()
				for trk in self.get_tracks():
					trk.undo_buff.add_state()
					trk.optimise()

			if mod.active_track:
				self.redraw_track(mod.active_track.trk)

		if cfg.key["fullscreen"].matches(event):
			if mod.mainwin.fs:
				mod.mainwin.unfullscreen()
				mod.mainwin.fs = False
			else:
				mod.mainwin.fullscreen()
				mod.mainwin.fs = True
			return True

		if cfg.key["exit_edit"].matches(event):
			if mod.active_track:
				#if mod.active_track.edit:
				return mod.active_track.on_key_press(widget, event)

		if cfg.key["reset"].matches(event):
			if not mod.play:
				mod.reset()
			return True

		if cfg.key["sequence_double"].matches(event):
			self.double()
			return True

		if cfg.key["sequence_halve"].matches(event):
			self.halve()
			return True


		if cfg.key["undo"].matches(event):
			if mod.active_track:
				return mod.active_track.on_key_press(widget, event)

		if cfg.key["zoom_in"].matches(event):
			self.zoom(1)
			return True

		if cfg.key["zoom_out"].matches(event):
			self.zoom(-1)
			return True

		if cfg.key["channel_up"].matches(event):
			if mod.active_track:
				mod.active_track.trk.channel = min(mod.active_track.trk.channel + 1, 16)
				self.prop_view.redraw()
			return True

		if cfg.key["channel_down"].matches(event):
			if mod.active_track:
				mod.active_track.trk.channel = max(mod.active_track.trk.channel - 1, 1)
				self.prop_view.redraw()
			return True

		if cfg.key["port_up"].matches(event):
			if mod.active_track:
				mod.active_track.trk.port = min(mod.active_track.trk.port + 1, mod.nports - 1)
				self.prop_view.redraw()
			return True

		if cfg.key["port_down"].matches(event):
			if mod.active_track:
				mod.active_track.trk.port = max(mod.active_track.trk.port - 1, 0)
				self.prop_view.redraw()
			return True

		if cfg.key["def_port_up"].matches(event):
			cfg.default_midi_out_port = min(max(cfg.default_midi_out_port + 1, 0), mod.max_ports - 1)
			mod.set_default_midi_port(cfg.default_midi_out_port)
			return True

		if cfg.key["def_port_down"].matches(event):
			cfg.default_midi_out_port = min(max(cfg.default_midi_out_port - 1, 0), mod.max_ports - 1)
			mod.set_default_midi_port(cfg.default_midi_out_port)
			return True

		if cfg.key["track_add"].matches(event):
			self._side_prop.add_track()
			return True

		if cfg.key["track_clone"].matches(event):
			if mod.active_track:
				self._side_prop.clone_track(mod.active_track)
			return True

		if cfg.key["track_del"].matches(event):
			if mod.active_track:
				self.del_track(mod.active_track.trk)
			return True

		if cfg.key["track_expand"].matches(event):
			if mod.active_track:
				self.expand_track(mod.active_track.trk)
			return True

		if cfg.key["track_shrink"].matches(event):
			if mod.active_track:
				self.shrink_track(mod.active_track.trk)
			return True

		if cfg.key["track_move_left"].matches(event):
			if mod.active_track:
				self.prop_view.move_left(mod.active_track.trk)
			return True

		if cfg.key["track_move_right"].matches(event):
			if mod.active_track:
				self.prop_view.move_right(mod.active_track.trk)
			return True

		if cfg.key["track_move_first"].matches(event):
			if mod.active_track:
				self.prop_view.move_first(mod.active_track.trk)
			return True

		if cfg.key["track_move_last"].matches(event):
			if mod.active_track:
				self.prop_view.move_last(mod.active_track.trk)
			return True

		if cfg.key["skip_up"].matches(event):
			cfg.skip += 1
			return True

		if cfg.key["skip_down"].matches(event):
			cfg.skip -= 1
			return True

		if cfg.key["quit"].matches(event):
				mod.mainwin.close()
				return True

		if cfg.key["octave_up"].matches(event):
			cfg.octave += 1
			if cfg.octave > 8:
				cfg.octave = 8
			return True

		if cfg.key["octave_down"].matches(event):
			cfg.octave -= 1
			if cfg.octave < 0:
				cfg.octave = 0
			return True

		if cfg.key["bpm_up"].matches(event):
			mod.bpm = mod.bpm + 1
			mod.mainwin.adj.set_value(mod.bpm)
			return True

		if cfg.key["bpm_down"].matches(event):
			mod.bpm = mod.bpm - 1
			mod.mainwin.adj.set_value(mod.bpm)
			return True

		if cfg.key["bpm_frac_up"].matches(event):
			mod.bpm = mod.bpm + .01
			mod.mainwin.adj.set_value(mod.bpm)
			return True

		if cfg.key["bpm_frac_down"].matches(event):
			mod.bpm = mod.bpm - .01
			mod.mainwin.adj.set_value(mod.bpm)
			return True

		if cfg.key["bpm_10_up"].matches(event):
			mod.bpm = mod.bpm + 10
			mod.mainwin.adj.set_value(mod.bpm)
			return True

		if cfg.key["bpm_10_down"].matches(event):
			mod.bpm = mod.bpm - 10
			mod.mainwin.adj.set_value(mod.bpm)
			return True

		if cfg.key["highlight_up"].matches(event):
			cfg.highlight = min(cfg.highlight + 1, 32)
			return True

		if cfg.key["highlight_down"].matches(event):
			cfg.highlight = max(cfg.highlight - 1, 1)
			return True

		# velocities fall through if not in edit mode

		ed = False
		if mod.active_track:
			if mod.active_track.edit:
				if mod.active_track.edit[0] < len(mod.active_track.trk):
					if	mod.active_track.trk[min(mod.active_track.edit[0], len(mod.active_track.trk))]\
														[mod.active_track.edit[1]].type == 1:
						ed = True
			if mod.active_track.select_end:
				ed = True

		if not ed:
			if cfg.key["velocity_up"].matches(event):
				cfg.velocity = min(cfg.velocity + 1, 127)
				return True

			if cfg.key["velocity_10_up"].matches(event):
				cfg.velocity = min(cfg.velocity + 10, 127)
				return True

			if cfg.key["velocity_down"].matches(event):
				cfg.velocity = max(cfg.velocity - 1, 0)
				return True

			if cfg.key["velocity_10_down"].matches(event):
				cfg.velocity = max(cfg.velocity - 10, 0)
				return True

		if event.keyval >= 65470 and event.keyval <= 65477:
			t = event.keyval - 65470
			if t < len(self.seq):
				self.seq[t].trigger()
				self.prop_view.redraw()

		# do we enter editing mode?
		if mod.active_track:
			if not mod.active_track.edit:
				vals = [65364, 65362, 65363, 65361, 65366, 65365, 65360, 65367]

				for v in vals:
					if event.keyval == v:
						if not mod.active_track.select_start:
							mod.active_track.edit = 0, 0
							mod.active_track.redraw(0)
							return True

		if mod.active_track:
			return mod.active_track.on_key_press(widget, event)

		return False

	def on_key_release(self, widget, event):
		if mod.active_track:
			return mod.active_track.on_key_release(widget, event)

		return False

	def size_up(self):
		pass

	def size_down(self):
		pass

	def zoom(self, i):
		cfg.seq_font_size += i

		if cfg.seq_font_size < 1:
			cfg.seq_font_size = 1

		cfg.pointer_height = .7 * cfg.seq_font_size
		self.redraw_track(None)
		self._side_prop.redraw()
		self.prop_view.redraw()
		#self._status_bar.queue_resize()

	def on_scroll(self, widget, event):
		if event.state & Gdk.ModifierType.CONTROL_MASK: # we're zooming!
			if event.delta_y > 0:
				self.zoom(-1)

			if event.delta_y < 0:
				self.zoom(1)

			return True

		if mod.active_track:
			return mod.active_track.on_scroll(event)

		return False

	def on_motion(self, widget, event):
		#mod.clear_popups()
		self._sv.grab_focus()

	def add_track(self, trk):
		t = TrackView(self.seq, trk, self)

		if trk:
			self._track_box.pack_start(t, False, True, 0)
		else:
			self._side_box.pack_start(t, False, True, 0)

		if trk:
			self.prop_view.add_track(trk, t)

			if cfg.new_tracks_left and mod.record != 2:
				self.prop_view.move_first(trk)

		self.recalculate_row_spacing()
		t.show()
		return t

	def expand_track(self, trk):
		trk.add_column()
		self.redraw_track(trk)
		self.prop_view.redraw()

	def double(self):
		self.seq.double()
		self._side_prop.popover.length_adj.set_value(self.seq.length)
		self.recalculate_row_spacing()

		for trk in self.get_tracks():
			trk.resetundo()

		self.redraw_track()

	def halve(self):
		TrackView.leave_all()
		self.seq.halve()
		self._side_prop.popover.length_adj.set_value(self.seq.length)
		self.recalculate_row_spacing()

		for trk in self.get_tracks():
			trk.resetundo()

		self.redraw_track()

	def shrink_track(self, trk):
		trk.del_column()

		for wdg in self.get_tracks():
			if wdg.trk.index == trk.index:
				if wdg.edit:
					wdg.edit = min(wdg.edit[0], len(trk) -1), wdg.edit[1]

		self.redraw_track(trk)
		self.prop_view.redraw()

	def del_track(self, trk):
		restore_track_index = -1
		restore_edit = None
		if mod.active_track:
			restore_track_index = mod.active_track.trk.index
			if mod.active_track.edit:
				restore_edit = mod.active_track.edit

		del(mod.extras[self.seq.index][trk.index])
		for i in sorted(mod.extras[self.seq.index]):
			if i > trk.index:
				mod.extras[self.seq.index][i - 1] = mod.extras[self.seq.index][i]
				del(mod.extras[self.seq.index][i])

		TrackView.leave_all()
		mod.active_track = None
		self.prop_view.del_track(trk)

		w = None
		for wdg in self.get_tracks():
			if wdg.trk.index == trk.index:
				w = wdg

		if w:
			TrackView.track_views.remove(w)
			self.seq.del_track(trk.index)
			w.destroy()

			for i, wdg in enumerate(self.get_tracks()):
				wdg.trk.index = i

		if restore_track_index > -1:
			restore_track_index = min(restore_track_index, len(self.seq) - 1)
			if restore_track_index > -1:
				mod.active_track = self.get_tracks()[restore_track_index]
				if restore_edit:
					mod.active_track.edit = min(restore_edit[0], len(mod.active_track.trk) - 1), min(restore_edit[1], mod.active_track.trk.nrows - 1)

		self.recalculate_row_spacing()

	def get_track_view(self, trk):
		for wdg in self.get_tracks():
			if wdg.trk.index == trk.index:
				return wdg

	def change_active_track(self, trk):
		ac = mod.active_track
		mod.active_track = trk

		if ac != trk:
			self.seq.set_midi_focus(trk.trk.index)
			if ac:
				ac.pmp.silence()

			if trk._surface:
				self.prop_view.redraw()

			#mod.clear_popups()

	# trk == none - do all

	def redraw_track(self, trk = None):
		redr = False

		for wdg in self.get_tracks(True):
			rdr = False

			if not trk:
				rdr = True
			else:
				if wdg.trk:
					if wdg.trk.index == trk.index:
						rdr = True

			if rdr:
				wdg.redraw_full()
				if trk:
					self.prop_view.redraw(trk.index)
				#w = wdg.width

				#if trk and w != wdg.width:
				#	self.prop_view.redraw(trk.index)

		if not trk:
			self.prop_view.redraw()

		self.queue_draw()

	def build(self):
		self.prop_view.seq = self.seq
		self._side_prop.seq = self.seq
		self._side_prop.popover.seq = self.seq

		self.add_track(None)
		for trk in self.seq:
			self.add_track(trk)

	def clear(self):
		while len(self.seq):
			self.del_track(self.seq[0])

		self._side_box.remove(self._side_box.get_children()[0])

	def load(self, filename):
		self.clear()
		mod.load(filename)
		self.seq = mod[0]
		self.build()

	def recalculate_row_spacing(self):
		if not self.get_realized():
			return

		minspc = 1.0

		for wdg in self.get_tracks(True):
			if wdg.trk == None:
				spc = 1.0
			else:
				spc = wdg.trk.nsrows / wdg.trk.nrows
			wdg.spacing = spc

			if 0 < spc < minspc:
				minspc = spc

		if minspc < 1.0:
			for wdg in self.get_tracks(True):
				wdg.spacing /= minspc

		self.redraw_track(None)
		self.queue_draw()

	def auto_scroll(self, trk):
		w = self._sv.get_allocated_width()
		h = self._sv.get_allocated_height()

		hadj = self._sv.get_hadjustment()
		vadj = self._sv.get_vadjustment()

		if not self.autoscroll_req:
			return

		r = trk.edit[1]
		if trk.keyboard_focus:
			r = trk.keyboard_focus.edit

		vtarget = (r * trk.txt_height) + trk.txt_height / 2.0
		trk_height = trk.txt_height * trk.trk.nrows
		vtarget = vtarget - (h / 2.0)

		if vtarget < 0:
			vtarget = 0

		if vtarget > trk_height - h:
			vtarget = trk_height - h

		vt = vtarget
		vtarget = vadj.get_value() + ((vtarget - vadj.get_value()) * cfg.auto_scroll_delay)

		vadj.set_value(vtarget)

		hextra = 0 #trk.width / 2
		htarget = (trk.edit[0] * trk.txt_width) + hextra
		if trk.keyboard_focus:
			htarget = trk.keyboard_focus.x_from + hextra

		for wdg in self.get_tracks()[:trk.trk.index]:
			htarget += wdg.width

		trk_width = trk.txt_width * len(trk.trk)
		htarget = htarget - (w / 2.0)

		if htarget < 0:
			htarget = 0

		if htarget > self._track_box.get_allocated_width() - w:
			htarget = self._track_box.get_allocated_width() - w

		ht = htarget
		htarget = hadj.get_value() + ((htarget - hadj.get_value()) * cfg.auto_scroll_delay)

		if abs(vt - vtarget) < .001 and abs(ht - htarget) < .001:
			self.autoscroll_req = False
			self.last_autoscroll_r = r

		hadj.set_value(htarget)

		self._sv.set_hadjustment(hadj)
		self._sv.set_vadjustment(vadj)

	def tick(self, wdg, param):
		for wdg in self.get_tracks(True):
			wdg.tick()
			if wdg.edit and wdg.trk:
				self.auto_scroll(wdg)

		# this is for things like start/stop/record/rewind/clear track
		if not mod.gui_midi_capture:
			midin = mod.get_midi_in_event()
			while(midin):
				if mod.active_track:
					mod.active_track.midi_in(midin)

				#print(midin)

				for k in cfg.midi_in.keys():
					m = cfg.midi_in[k]
					if midin["channel"] == m[0]:
						if midin["type"] == m[1]:
							if midin["note"] == m[2]:
								if midin["velocity"] == m[3]:
									class kbd_evt():
										pass

									cfg_evt = cfg.key[k]

									kev = kbd_evt()

									kev.keyval = Gdk.keyval_from_name(cfg_evt.key)
									kev.state = Gdk.ModifierType.META_MASK

									if cfg_evt.shift:
										kev.state = kev.state | Gdk.ModifierType.SHIFT_MASK

									if cfg_evt.ctrl:
										kev.state = kev.state | Gdk.ModifierType.CONTROL_MASK

									if cfg_evt.alt:
										kev.state = kev.state | Gdk.ModifierType.MOD1_MASK

									self.on_key_press(self, kev)

				midin = mod.get_midi_in_event()

		if mod.record > -1:
			for trk in self.get_tracks():
				redr_props = False
				r = trk.trk.get_rec_update()
				while r:
					trk.configure()
					trk.redraw(r["row"])

					if mod.record:
						trk.undo_buff.add_state()
						redr_props = True

						ctr = r["col"] - len(trk.trk)
						if ctr > len(trk.controller_editors):
							trk.redraw_full()

					r = trk.trk.get_rec_update()

				if redr_props:
					self.prop_view.redraw(trk.trk.index)
					trk.tick()
					#trk.undo_buff.add_state()

			if len(self.get_tracks()) != len(self.seq):
				for trk in self.seq:
					found = False
					for t in self.get_tracks():
						if trk.index == t.trk.index:
							found = True

					if not found:
						self.add_track(trk)

		return True

	def on_draw(self, widget, cr):
		w = widget.get_allocated_width()
		h = widget.get_allocated_height()

		cr.set_source_rgb(*(col * cfg.intensity_background for col in cfg.colour))
		cr.rectangle(0, 0, w, h)
		cr.fill()

	def get_tracks(self, with_side_view = False):
		ret = []
		for wdg in self._track_box.get_children():
			ret.append(wdg)

		if with_side_view:
			if len(self._side_box.get_children()):
				ret.append(self._side_box.get_children()[0])

		return ret

	def on_enter(self, wdg, prm):
		self._sv.grab_focus()
