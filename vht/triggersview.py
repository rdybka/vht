# triggersview.py - Valhalla Tracker
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
from gi.repository import Gtk, Gio, Gdk

from vht import cfg, mod

class TriggersView(Gtk.Grid):
	def __init__(self, trk, trkview, parent):
		super(TriggersView, self).__init__()

		self.set_orientation(Gtk.Orientation.VERTICAL)

		self.parent = parent
		self.trk = trk
		self.trkview = trkview
		self.capture = -1
		self.butt_handler = None

		self.set_column_spacing(3)
		self.set_row_spacing(3)
		self.set_column_homogeneous(False)
		self.set_row_homogeneous(False)

		self.attach(Gtk.Label("mute:"), 0, 0, 1, 1)
		self.attach(Gtk.Label("cue:"), 0, 1, 1, 1)
		self.attach(Gtk.Label("play:"), 0, 2, 1, 1)

		entry_wc = 20

		# mute
		self.mute_capture_button = Gtk.ToggleButton()
		self.mute_capture_button.set_tooltip_markup(cfg.tooltip_markup % ("capture"))
		icon = Gio.ThemedIcon(name="media-record")
		image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
		self.mute_capture_button.add(image)
		self.mute_capture_button.connect("toggled", self.on_capture_toggled, 0)

		self.attach(self.mute_capture_button, 1, 0, 1, 1)

		self.mute_entry = Gtk.Entry()
		self.mute_entry.props.sensitive = False

		self.mute_entry.set_width_chars(entry_wc)

		self.attach(self.mute_entry, 3, 0, 1, 1)

		button = Gtk.Button()
		icon = Gio.ThemedIcon(name="edit-delete")
		image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
		button.add(image)
		button.set_tooltip_markup(cfg.tooltip_markup % ("clear"))
		button.connect("clicked", self.on_clear_clicked, 0)
		self.attach(button, 2, 0, 1, 1)

		# cue
		self.cue_capture_button = Gtk.ToggleButton()
		self.cue_capture_button.set_tooltip_markup(cfg.tooltip_markup % ("capture"))
		icon = Gio.ThemedIcon(name="media-record")
		image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
		self.cue_capture_button.add(image)
		self.cue_capture_button.connect("toggled", self.on_capture_toggled, 1)
		self.attach(self.cue_capture_button, 1, 1, 1, 1)

		self.cue_entry = Gtk.Entry()
		self.cue_entry.props.sensitive = False

		self.cue_entry.set_width_chars(entry_wc)
		self.attach(self.cue_entry, 3, 1, 1, 1)

		button = Gtk.Button()
		icon = Gio.ThemedIcon(name="edit-delete")
		image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
		button.add(image)
		button.set_tooltip_markup(cfg.tooltip_markup % ("clear"))
		button.connect("clicked", self.on_clear_clicked, 1)
		self.attach(button, 2, 1, 1, 1)

		# play
		self.play_capture_button = Gtk.ToggleButton()
		self.play_capture_button.set_tooltip_markup(cfg.tooltip_markup % ("capture"))
		icon = Gio.ThemedIcon(name="media-record")
		image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
		self.play_capture_button.add(image)
		self.play_capture_button.connect("toggled", self.on_capture_toggled, 2)
		self.attach(self.play_capture_button, 1, 2, 1, 1)

		self.play_midi_entry = Gtk.Entry()
		self.play_midi_entry.props.sensitive = False
		self.play_midi_entry.set_width_chars(entry_wc)
		self.attach(self.play_midi_entry, 3, 2, 1, 1)

		self.play_kp_entry = Gtk.Entry()
		self.play_kp_entry.set_tooltip_markup(cfg.tooltip_markup % ("keypad"))
		self.play_kp_entry.props.sensitive = False
		self.play_kp_entry.set_width_chars(1)
		self.attach(self.play_kp_entry, 4, 2, 1, 1)

		button = Gtk.Button()
		icon = Gio.ThemedIcon(name="edit-delete")
		image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
		button.add(image)
		button.set_tooltip_markup(cfg.tooltip_markup % ("clear"))
		button.connect("clicked", self.on_clear_clicked, 2)
		self.attach(button, 2, 2, 1, 1)

		self.play_mode_cb = Gtk.ComboBoxText()
		for m in ["on/off", "hold"]:
			self.play_mode_cb.append_text(m)

		self.play_mode_cb.set_active(trk.trg_playmode)
		self.play_mode_cb.connect("changed", self.on_play_mode_changed)
		self.play_mode_cb.set_tooltip_markup(cfg.tooltip_markup % ("play mode"))
		self.attach(self.play_mode_cb, 1, 3, 2, 1)

		self.quantise_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 16, 1)
		self.quantise_scale.set_value(trk.trg_quantise)
		self.quantise_scale.set_tooltip_markup(cfg.tooltip_markup % ("quantise"))
		self.quantise_scale.connect("value-changed", self.on_quantise_changed)
		self.attach(self.quantise_scale, 3, 3, 1, 1)

		# autoplay
		self.timeline_toggle = Gtk.CheckButton("timeline")
		self.timeline_toggle.connect("toggled", self.on_bool_toggled, 0)
		self.timeline_toggle.set_active(trk.trg_timeline)
		self.attach(self.timeline_toggle, 1, 4, 2, 1)

		self.letring_toggle = Gtk.CheckButton("let ring")
		self.letring_toggle.connect("toggled", self.on_bool_toggled, 1)
		self.letring_toggle.set_active(trk.trg_letring)
		self.attach(self.letring_toggle, 3, 4, 1, 1)

		self.loop_toggle = Gtk.CheckButton("loop")
		self.loop_toggle.set_active(trk.loop)
		self.loop_toggle.connect("toggled", self.on_bool_toggled, 2)
		self.attach(self.loop_toggle, 4, 4, 1, 1)

		self.refresh_desc()

		self.show_all()

	@staticmethod
	def desc_trigger(trig):
		knob_char = "ctrl"
		note_char = "note"
		desc = ""
		if trig[0] == 1:
			notes = ['C-', 'C#' , 'D-', 'D#', 'E-', 'F-', 'F#', 'G-', 'G#', 'A-', 'A#', 'B-']
			note = trig[2] % 12
			octave =trig[2] // 12
			strrep = ""
			if octave < 10:
				strrep = notes[note]+str(octave)
			else:
				strrep = notes[note]+'A'

			desc = "ch:%02d %s:%03d [%3s]" % (trig[1], note_char, trig[2], strrep)

		if trig[0] == 4:
			desc = "ch:%02d %s:%03d" % (trig[1], knob_char, trig[2])

		return desc

	def refresh_desc(self):
		self.mute_entry.props.text = TriggersView.desc_trigger(self.trk.get_trig(0))
		self.cue_entry.props.text = TriggersView.desc_trigger(self.trk.get_trig(1))
		self.play_midi_entry.props.text = TriggersView.desc_trigger(self.trk.get_trig(2))
		if "kp" in mod.extras[self.parent.parent.seq.index][self.trk.index]:
			if mod.extras[self.parent.parent.seq.index][self.trk.index]["kp"] > -1:
				self.play_kp_entry.props.text = str(mod.extras[self.parent.parent.seq.index][self.trk.index]["kp"])

	def on_clear_clicked(self, wdg, c):
		self.trk.set_trig(c, 0, 0, 0)
		self.refresh_desc()
		if c is 2:
			self.play_kp_entry.props.text = ""
			mod.extras[self.parent.parent.seq.index][self.trk.index]["kp"] = -1

	def on_bool_toggled(self, wdg, t):
		if t == 0:
			self.trk.trg_timeline = 1 if wdg.get_active() else 0

		if t == 1:
			self.trk.trg_letring = 1 if wdg.get_active() else 0

		if t == 2:
			self.trk.loop = 1 if wdg.get_active() else 0

	def on_quantise_changed(self, adj):
		self.trk.trg_quantise = int(adj.get_value())

	def on_play_mode_changed(self, wdg):
		self.trk.trg_playmode = wdg.get_active()

	def on_capture_toggled(self, wdg, capt):
		if wdg.get_active():
			mod.gui_midi_capture = True
			self.capture = capt
			self.add_tick_callback(self.tick)
			if capt == 0:
				self.cue_capture_button.set_active(False)
				self.play_capture_button.set_active(False)

			if capt == 1:
				self.mute_capture_button.set_active(False)
				self.play_capture_button.set_active(False)

			if capt == 2:
				self.cue_capture_button.set_active(False)
				self.mute_capture_button.set_active(False)
				self.connect("key-press-event", self.on_key_press)
		else:
			if capt == self.capture:
				self.capture = -1
				mod.gui_midi_capture = False

	def on_key_press(self, wdg, evt):
		if self.capture == 2:
			# let's hardcode some shit
			k = evt.keyval
			if 65456 <= k <= 65465:
				kp = k - 65456
				self.play_kp_entry.props.text = str(kp)
				mod.extras[self.parent.parent.seq.index][self.trk.index]["kp"] = kp
				return True

		return False

	def tick(self, wdg, param):
		if self.capture == -1:
			self.mute_capture_button.set_active(False)
			self.cue_capture_button.set_active(False)
			self.play_capture_button.set_active(False)
			return False

		midin = mod.get_midi_in_event()

		while midin:
			if midin["type"] in [1, 4]:
				if self.capture > -1:
					self.trk.set_trig(self.capture, midin["type"], midin["channel"], midin["note"])
					self.refresh_desc()

			midin = mod.get_midi_in_event()

		return True
