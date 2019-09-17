# statusbar.py - Valhalla Tracker
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
from gi.repository import Gdk, Gtk, Gio
import cairo

from vht import *
from vht.trackview import TrackView
from vht.pulsar import Pulsar

class StatusBar(Gtk.DrawingArea):
	def __init__(self):
		super(StatusBar, self).__init__()

		self.set_events(Gdk.EventMask.POINTER_MOTION_MASK |
			Gdk.EventMask.SCROLL_MASK |
			Gdk.EventMask.LEAVE_NOTIFY_MASK |
			Gdk.EventMask.BUTTON_PRESS_MASK |
			Gdk.EventMask.BUTTON_RELEASE_MASK)

		self.connect("draw", self.on_draw)
		self.connect("configure-event", self.on_configure)
		self.connect("motion-notify-event", self.on_motion)
		self.connect("scroll-event", self.on_scroll)
		self.connect("leave-notify-event", self.on_leave)
		self.connect("button-press-event", self.on_button_press)
		self.connect("button-release-event", self.on_button_release)
		self.connect("query-tooltip", self.on_tooltip)

		self._surface = None
		self._context = None
		self.min_char_width = 75

		self.pos = []
		self.active_field = None
		self.last_active_field = None
		self.add_tick_callback(self.tick)
		self.set_has_tooltip(True)
		self.tt_rect = Gdk.Rectangle()
		self.tt_txt = None

		self.pulse = Pulsar(mod.rpb)

	def redraw(self):
		cr = self._context
		w = self.get_allocated_width()
		h = self.get_allocated_height()

		(x, y, width, height, dx, dy) = cr.text_extents("0" * self.min_char_width)

		self.set_size_request(1, height * 1.5 * cfg.seq_spacing)

		bar_col = cfg.colour
		intensity = 1.0
		if mod.record:
			bar_col = cfg.record_colour
			intensity = self.pulse.intensity(mod[mod.curr_seq].pos)

		gradient = cairo.LinearGradient(0, 0, 0, h)
		gradient.add_color_stop_rgb(0, *(col * cfg.intensity_background * intensity for col in bar_col))
		gradient.add_color_stop_rgb(.3, *(col *  cfg.intensity_txt * intensity for col in bar_col))
		gradient.add_color_stop_rgb(.7, *(col *  cfg.intensity_txt * intensity for col in bar_col))

		gradient.add_color_stop_rgb(1.0, *(col * cfg.intensity_background for col in bar_col))

		cr.set_source(gradient)

		cr.rectangle(0, 0, w, h)
		cr.fill()

		trk = mod.active_track

		t = 0
		r = 0
		c = 0
		cs = mod.curr_seq

		self.pos = []

		self.pos.append(0)
		xx = 0

		if trk:
			t = trk.trk.index
			if trk.edit:
				c = trk.edit[0]
				r = trk.edit[1]

		txt = "%02d:%02d:%02d:%03d" % (cs, t, c, r)
		h = ((height * 1.5 * cfg.seq_spacing) / 2.0) + (height / 2.0)

		intensity = 1.0 - intensity

		if mod.record:
			cr.set_source_rgb(*(col * intensity for col in cfg.record_colour))
		else:
			cr.set_source_rgb(*(col * 0 for col in cfg.colour))

		(x, y, width, height, dx, dy) = cr.text_extents(txt)
		cr.move_to(self.pos[-1], h)
		cr.show_text(txt)
		xx += dx
		self.pos.append(xx)

		if self.active_field == 1:
			cr.set_source_rgb(*(col * cfg.intensity_txt_highlight for col in cfg.star_colour))
		else:
			cr.set_source_rgb(*(col * intensity for col in cfg.record_colour))

		txt = " oct:%d" % cfg.octave
		(x, y, width, height, dx, dy) = cr.text_extents(txt)
		cr.move_to(self.pos[-1], h)
		cr.show_text(txt)
		xx += dx
		self.pos.append(xx)

		if self.active_field == 2:
			cr.set_source_rgb(*(col * cfg.intensity_txt_highlight for col in cfg.star_colour))
		else:
			cr.set_source_rgb(*(col * intensity for col in cfg.record_colour))

		txt = " vel:%d" % cfg.velocity
		(x, y, width, height, dx, dy) = cr.text_extents(txt)
		cr.move_to(self.pos[-1], h)
		cr.show_text(txt)
		xx += dx
		self.pos.append(xx)

		if self.active_field == 3:
			cr.set_source_rgb(*(col * cfg.intensity_txt_highlight for col in cfg.star_colour))
		else:
			cr.set_source_rgb(*(col * intensity for col in cfg.record_colour))

		txt = " skp:%d" % cfg.skip
		(x, y, width, height, dx, dy) = cr.text_extents(txt)
		cr.move_to(self.pos[-1], h)
		cr.show_text(txt)
		xx += dx
		self.pos.append(xx)

		if self.active_field == 4:
			cr.set_source_rgb(*(col * cfg.intensity_txt_highlight for col in cfg.star_colour))
		else:
			cr.set_source_rgb(*(col * intensity for col in cfg.record_colour))

		txt = " hig:%d" % mod.mainwin._sequence_view.highlight

		if mod.mainwin._sequence_view.highlight == 1:
			txt = " hig:0"

		(x, y, width, height, dx, dy) = cr.text_extents(txt)
		cr.move_to(self.pos[-1], h)
		cr.show_text(txt)
		xx += dx
		self.pos.append(xx)

		if self.active_field == 5:
			cr.set_source_rgb(*(col * cfg.intensity_txt_highlight for col in cfg.star_colour))
		else:
			cr.set_source_rgb(*(col * intensity for col in cfg.record_colour))

		txt = " bpm:%6.2f" % mod.bpm
		(x, y, width, height, dx, dy) = cr.text_extents(txt)
		cr.move_to(self.pos[-1], h)
		cr.show_text(txt)
		xx += dx
		self.pos.append(xx)

		if self.active_field == 6:
			cr.set_source_rgb(*(col * cfg.intensity_txt_highlight for col in cfg.star_colour))
		else:
			cr.set_source_rgb(*(col * intensity for col in cfg.record_colour))

		txt = " rpb:%d" % mod.rpb
		(x, y, width, height, dx, dy) = cr.text_extents(txt)
		cr.move_to(self.pos[-1], h)
		cr.show_text(txt)
		xx += dx
		self.pos.append(xx)

		if self.active_field == 7:
			cr.set_source_rgb(*(col * cfg.intensity_txt_highlight for col in cfg.star_colour))
		else:
			cr.set_source_rgb(*(col * intensity for col in cfg.record_colour))

		txt = " prt:%d" % cfg.default_midi_out_port
		(x, y, width, height, dx, dy) = cr.text_extents(txt)
		cr.move_to(self.pos[-1], h)
		cr.show_text(txt)
		xx += dx
		self.pos.append(xx)

		if mod.record:
			cr.set_source_rgb(*(col * intensity for col in cfg.record_colour))
		else:
			cr.set_source_rgb(*(col * intensity for col in cfg.colour))

		txt = "%02d:%03d.%03d ***" % (cs, int(mod[cs].pos), (mod[cs].pos - int(mod[cs].pos)) * 1000)
		(x, y, width, height, dx, dy) = cr.text_extents(txt)
		cr.move_to(w - dx, h)
		cr.show_text(txt)

		cr.set_source_rgb(*(col * 0 for col in cfg.colour))

		cr.move_to(0, 0)
		cr.line_to(w, 0)
		cr.stroke()

		self.queue_draw()

	def tick(self, wdg, param):
		self.redraw()
		return 1

	def on_configure(self, wdg, event):
		if self._surface:
			self._surface.finish()

		w = wdg.get_allocated_width()
		h = wdg.get_allocated_width()

		self.tt_rect.height = h

		self._surface = wdg.get_window().create_similar_surface(cairo.CONTENT_COLOR, w, h)

		self._context = cairo.Context(self._surface)
		self._context.set_antialias(cairo.ANTIALIAS_NONE)
		self._context.set_line_width((cfg.seq_font_size / 6.0) * cfg.seq_line_width)

		self._context.select_font_face(cfg.seq_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)

		fs = cfg.status_bar_font_size
		fits = False
		while not fits:
			self._context.set_font_size(fs)
			(x, y, width, height, dx, dy) = self._context.text_extents("X" * self.min_char_width)
			if w > dx:
				fits = True
			else:
				fs -= 1

		self.redraw()
		return True

	def on_draw(self, widget, cr):
		cr.set_source_surface(self._surface, 0, 0)
		cr.paint()
		return False

	def on_motion(self, widget, event):
		self.active_field = None

		xx = 0
		af = -1
		for pos in self.pos:
			if event.x > xx and event.x < pos:
				self.active_field = af
				self.tt_rect.x = xx
				self.tt_rect.y = 0
				self.tt_rect.width = pos - xx

			xx = pos
			af += 1

		if self.last_active_field != self.active_field:
			if not self.active_field:
				self.tt_txt = None

			if self.active_field == 1:	# octave
				self.tt_txt = "<big>↑</big> %s\n<big>↓</big> %s" % (cfg.key["octave_up"], cfg.key["octave_down"])

			if self.active_field == 2:	# velocity
				self.tt_txt = "<big>⇑</big> %s\n<big>↑</big> %s\n<big>↓</big> %s\n<big>⇓</big> %s" % (cfg.key["velocity_10_up"], cfg.key["velocity_up"], cfg.key["velocity_down"], cfg.key["velocity_10_down"])

			if self.active_field == 3:	# skip
				self.tt_txt = "<big>↑</big> %s\n<big>↓</big> %s" % (cfg.key["skip_up"], cfg.key["skip_down"])

			if self.active_field == 4:	# highlight
				self.tt_txt = "<big>↑</big> %s\n<big>↓</big> %s" % (cfg.key["highlight_up"], cfg.key["highlight_down"])

			if self.active_field == 5:	# bpm
				self.tt_txt = "<big> ⇑</big> %s\n<big> ↑</big> %s\n<big>.↑</big> %s\n<big>.↓</big> %s\n<big> ↓</big> %s\n<big> ⇓</big> %s" % (cfg.key["bpm_10_up"], cfg.key["bpm_up"], cfg.key["bpm_frac_up"], cfg.key["bpm_frac_down"], cfg.key["bpm_down"], cfg.key["bpm_10_down"])

			if self.active_field == 6:	# rpb
				self.tt_txt = "<big>↑</big> %s\n<big>↓</big> %s" % (cfg.key["rpb_up"], cfg.key["rpb_down"])

			if self.active_field == 7:	# prt
				self.tt_txt = "<big>↑</big> %s\n<big>↓</big> %s" % (cfg.key["def_port_up"], cfg.key["def_port_down"])

			self.last_active_field = self.active_field

	def on_scroll(self, widget, event):
		if not self.active_field:
			return True

		up = event.direction ==  Gdk.ScrollDirection.UP
		down = event.direction ==  Gdk.ScrollDirection.DOWN

		if self.active_field == 1:
			if up:
				cfg.octave	= min(cfg.octave + 1, 8)
			if down:
				cfg.octave	= max(cfg.octave - 1, 0)

		if self.active_field == 2:
			if up:
				cfg.velocity = min(cfg.velocity + 1, 127)
			if down:
				cfg.velocity = max(cfg.velocity - 1, 0)

		if self.active_field == 3:
			if up:
				cfg.skip = min(cfg.skip + 1, 16)
			if down:
				cfg.skip = max(cfg.skip - 1, -16)

		if self.active_field == 4:
			aseq = mod.mainwin._sequence_view
			if up:
				aseq.highlight = min(aseq.highlight + 1, 32)
			if down:
				aseq.highlight = max(aseq.highlight - 1, 1)

			mod.mainwin._sequence_view.redraw_track()
			mod.extras[aseq.seq.index][-1]["highlight"] = aseq.highlight

		if self.active_field == 5:
			if up:
				mod.bpm = mod.bpm + 1
				mod.mainwin.adj.set_value(mod.bpm)
			if down:
				mod.bpm = mod.bpm - 1
				mod.mainwin.adj.set_value(mod.bpm)

		if self.active_field == 6:
			if up:
				mod.rpb += 1
			if down:
				mod.rpb -= 1

		if self.active_field == 7:
			if up:
				cfg.default_midi_out_port = min(max(cfg.default_midi_out_port + 1, 0), mod.max_ports - 1)
				mod.set_default_midi_port(cfg.default_midi_out_port)
			if down:
				cfg.default_midi_out_port = min(max(cfg.default_midi_out_port - 1, 0), mod.max_ports - 1)
				mod.set_default_midi_port(cfg.default_midi_out_port)

		return True

	def on_leave(self, wdg, prm):
		self.active_field = None

	def on_button_press(self, widget, event):
		pass

	def on_button_release(self, widget, event):
		up = down = False

		if event.button == 1:
			down = True

		if event.button == 3:
			up = True

		if self.active_field == 1:
			if up:
				cfg.octave	= min(cfg.octave + 1, 8)
			if down:
				cfg.octave	= max(cfg.octave - 1, 0)

		if self.active_field == 2:
			if up:
				cfg.velocity = min(cfg.velocity + 1, 127)
			if down:
				cfg.velocity = max(cfg.velocity - 1, 0)

		if self.active_field == 3:
			if up:
				cfg.skip = min(cfg.skip + 1, 16)
			if down:
				cfg.skip = max(cfg.skip - 1, -16)


		if self.active_field == 4:
			aseq = mod.mainwin._sequence_view
			if up:
				aseq.highlight = min(aseq.highlight + 1, 32)
			if down:
				aseq.highlight = max(aseq.highlight - 1, 1)

			mod.mainwin._sequence_view.redraw_track()
			mod.extras[aseq.seq.index][-1]["highlight"] = aseq.highlight
		
		if self.active_field == 5:
			if up:
				mod.bpm = mod.bpm + 1
				mod.mainwin.adj.set_value(mod.bpm)
			if down:
				mod.bpm = mod.bpm - 1
				mod.mainwin.adj.set_value(mod.bpm)

		if self.active_field == 6:
			if up:
				mod.rpb += 1
			if down:
				mod.rpb -= 1

		if self.active_field == 7:
			if up:
				cfg.default_midi_out_port = min(max(cfg.default_midi_out_port + 1, 0), mod.max_ports - 1)
				mod.set_default_midi_port(cfg.default_midi_out_port)
			if down:
				cfg.default_midi_out_port = min(max(cfg.default_midi_out_port - 1, 0), mod.max_ports - 1)
				mod.set_default_midi_port(cfg.default_midi_out_port)

	def on_tooltip(self, wdg, x, y, kbd, tt):
		if not self.active_field:
			return False

		if not self.tt_txt:
			return False

		tt.set_markup(cfg.tooltip_markup % (self.tt_txt))

		tt.set_tip_area(self.tt_rect)
		return True
