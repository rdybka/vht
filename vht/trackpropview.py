import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio
import cairo

from vht import *
from vht.trackpropviewpopover import TrackPropViewPopover
from vht.sequencepropviewpopover import SequencePropViewPopover
from vht.trackview import TrackView

class TrackPropView(Gtk.DrawingArea):
	def __init__(self, trk = None, trkview = None, seq = None, seqview = None, propview = None):
		super(TrackPropView, self).__init__()

		self.set_events(Gdk.EventMask.POINTER_MOTION_MASK |
			Gdk.EventMask.SCROLL_MASK |
			Gdk.EventMask.BUTTON_PRESS_MASK |
			Gdk.EventMask.BUTTON_RELEASE_MASK |
			Gdk.EventMask.LEAVE_NOTIFY_MASK |
			Gdk.EventMask.ENTER_NOTIFY_MASK |
			Gdk.EventMask.KEY_PRESS_MASK |
			Gdk.EventMask.KEY_RELEASE_MASK)

		self.connect("button-press-event", self.on_click)
		self.connect("motion-notify-event", self.on_mouse_move)
		self.connect("leave-notify-event", self.on_leave)
		self.connect("enter-notify-event", self.on_enter)
		self.connect("draw", self.on_draw)
		self.connect("configure-event", self.on_configure)

		self.add_tick_callback(self.tick)

		self.seq = seq
		self.trk = trk
		self.trkview = trkview
		self.propview = propview
		self.seqview = seqview
		self.txt_width = 0
		self.txt_height = 0
		self.button_rect = Gdk.Rectangle()
		self.button_highlight = False
		self._surface = None
		self._context = None

		self.popped = False

		if trk:
			self.popover = TrackPropViewPopover(self, trk)
		else:
			self.popover = SequencePropViewPopover(self, seq)

		self.popover.set_position(Gtk.PositionType.BOTTOM)
		self.popped = False


	def configure(self):
		if self._surface:
			self._surface.finish()

		if self.trkview:
			self._surface = self.get_window().create_similar_surface(cairo.CONTENT_COLOR,
				self.trkview.width,
				self.get_allocated_height())

			self.set_size_request(self.trkview.width, self.txt_height * 2 * cfg.seq_spacing)
		else:
			self._surface = self.get_window().create_similar_surface(cairo.CONTENT_COLOR,
				self.get_allocated_width(),
				self.get_allocated_height())

		self._context = cairo.Context(self._surface)
		self._context.set_antialias(cairo.ANTIALIAS_NONE)
		self._context.set_line_width((cfg.seq_font_size / 6.0) * cfg.seq_line_width)
		self._context.select_font_face(cfg.seq_font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)

	def on_configure(self, wdg, event):
		self.redraw()
		return True

	def add_track(self):
		port = 0
		channel = 1
		if (len(self.seq)):
			port = self.seq[-1].port
			channel = self.seq[-1].channel

		trk = self.seq.add_track(port, channel)
		self.seqview.add_track(trk)

	def clone_track(self, trk):
		ntrk = self.seq.clone_track(trk.trk)
		t = self.seqview.add_track(ntrk)
		t.show_controllers = trk.show_controllers
		t.show_pitchwheel = trk.show_pitchwheel
		t.show_notes = trk.show_notes
		t.show_timeshift = trk.show_timeshift

		# undo buffers
		trk.undo_buff.clone(t.undo_buff)
		trk.pitchwheel_editor.undo_buff.clone(t.pitchwheel_editor.undo_buff)

		for i, c in enumerate(trk.controller_editors):
			c.undo_buff.clone(t.controller_editors[i].undo_buff)

		t.redraw_full()

	def del_track(self):
		self.seqview.del_track(self.trk)

	def move_left(self):
		self.propview.move_left(self.trk)

	def move_right(self):
		self.propview.move_right(self.trk)

	def move_first(self):
		self.propview.move_first(self.trk)

	def move_last(self):
		self.propview.move_last(self.trk)

	def on_mouse_move(self, widget, data):
		if data.x >= self.button_rect.x:
			if data.x <= self.button_rect.x + self.button_rect.width:
				if data.y >= self.button_rect.y:
					if data.y <= self.button_rect.y + self.button_rect.height:
						if not self.popped:
							self.popover.pop()
							self.popped = True
							self.button_highlight = True
							self.redraw()
						return

		self.button_highlight = False
		self.redraw()

	def on_click(self, widget, data):
		if data.type != Gdk.EventType.BUTTON_PRESS:
			return

		if data.x >= self.button_rect.x:
			if data.x <= self.button_rect.x + self.button_rect.width:
				if data.y >= self.button_rect.y:
					if data.y <= self.button_rect.y + self.button_rect.height:
						if self.popped:
							self.popover.unpop()
							self.popped = False
							return
						else:
							mod.clear_popups()
							self.popover.pop()
							self.popped = True
							return

		if self.trk:
			self.trk.trigger()
			self.redraw()

	def redraw(self):
		self.configure()
		cr = self._context

		w = self.get_allocated_width()
		h = self.get_allocated_height()

		if self.trk:
			w = self.trkview.width

		self._context.set_font_size(cfg.seq_font_size)
		cr.set_source_rgb(*(col * cfg.intensity_background for col in cfg.colour))
		cr.rectangle(0, 0, w, h)
		cr.fill()

		active = False
		if mod.active_track == self.trkview:
			active = True

		if self.trk == None:
			(x, y, width, height, dx, dy) = cr.text_extents("00_|")
			self.txt_height = height
			self.txt_width = int(dx)

			self.set_size_request(self.txt_width, self.txt_height * 2 * cfg.seq_spacing)

			cr.set_source_rgb(*(col * cfg.intensity_background for col in cfg.colour))
			cr.rectangle(0, 0, w, h)
			cr.fill()

			if self.popped or self.button_highlight:
				cr.set_source_rgb(*(col * cfg.intensity_txt_highlight for col in cfg.star_colour))
			else:
				cr.set_source_rgb(*(col * cfg.intensity_txt / 2 for col in cfg.star_colour))

			cr.move_to(x, self.txt_height * cfg.seq_spacing)
			cr.show_text("vht")
			cr.move_to(x, self.txt_height * 2 * cfg.seq_spacing)
			cr.show_text("***")

			self.button_rect.width = width
			self.button_rect.height = height * cfg.seq_spacing
			self.button_rect.x = x;
			self.button_rect.y = height * cfg.seq_spacing
			self.popover.set_pointing_to(self.button_rect)

			self.button_rect.y = 0
			self.button_rect.height = height * cfg.seq_spacing * 2

			cr.set_line_width((cfg.seq_font_size / 6.0) * cfg.seq_line_width)
			(x, y, width, height, dx, dy) = cr.text_extents("|")
			cr.set_source_rgb(*(col * cfg.intensity_lines for col in cfg.colour))
			cr.set_antialias(cairo.ANTIALIAS_NONE)
			cr.move_to(self.txt_width - (dx / 2), self.txt_height * .3 * cfg.seq_spacing)
			cr.line_to(self.txt_width - (dx / 2), (self.seq.length) * self.txt_height * cfg.seq_spacing)
			cr.stroke()
			self.queue_draw()
			return

		(x, y, width, height, dx, dy) = cr.text_extents("000 00_|")
		if self.trkview.show_timeshift:
			(x, y, width, height, dx, dy) = cr.text_extents("000 000 00_./set|")

		self.txt_height = height
		self.txt_width = int(dx)
		self.width = self.trkview.width

		gradient = cairo.LinearGradient(0, 0, 0, h)

		gradient.add_color_stop_rgb(0.0, *(col * cfg.intensity_background for col in cfg.colour))

		colour = cfg.colour

		if self.trk.playing:
			gradient.add_color_stop_rgb(0.1, *(col *  cfg.intensity_txt_highlight for col in colour))
			gradient.add_color_stop_rgb(0.4, *(col *  cfg.intensity_txt_highlight for col in colour))
		else:
			gradient.add_color_stop_rgb(0.1, *(col *  cfg.intensity_txt for col in colour))

		gradient.add_color_stop_rgb(1.0, *(col * cfg.intensity_background for col in colour))

		cr.set_source(gradient)

		(x, y, width, height, dx, dy) = cr.text_extents("0")

		cr.rectangle(0, 0, self.width - width, h)
		cr.fill()

		if active:
			alpha = .8
			gradient = cairo.LinearGradient(0, 0, 0, self.txt_height * 2)
			gradient.add_color_stop_rgba(0, *(col *  cfg.intensity_txt_highlight for col in cfg.record_colour), alpha)
			gradient.add_color_stop_rgba(.1, *(col *  cfg.intensity_txt_highlight for col in cfg.record_colour), alpha)
			gradient.add_color_stop_rgba(.8, *(col *  cfg.intensity_txt_highlight * .4 for col in cfg.record_colour), alpha)

			gradient.add_color_stop_rgba(1.0, *(col *  cfg.intensity_background for col in cfg.record_colour), alpha)
			cr.set_source(gradient)

			yy = 1.3
			c = len(self.trk)
			xfrom = - width * 2
			xto = self.trkview.txt_width * c

			kf = self.trkview.keyboard_focus
			if kf:
				xfrom = kf.x_from
				xto = kf.x_to + width
				xfrom -= width

			cr.move_to(xfrom, self.txt_height * yy * 2.5)
			cr.curve_to(xfrom + width, self.txt_height * 1.8,
					xfrom + width, self.txt_height * yy,
					xfrom + (width * 1.8), self.txt_height * yy)

			cr.line_to(xto - (width * 1.8), self.txt_height * yy)
			cr.curve_to(xto - width, self.txt_height * yy,
					xto - width, self.txt_height * 1.8,
					xto, self.txt_height * 2.5)

			cr.line_to(self.width - width, self.txt_height * yy * 10)
			cr.line_to(-1, self.txt_height * yy * 10)
			cr.stroke_preserve()
			cr.fill()

		if active and self.trkview.keyboard_focus:
			redfrom = 0
			redto = 0

		(x, y, width, height, dx, dy) = cr.text_extents("000 000|")
		if self.trkview.show_timeshift:
			(x, y, width, height, dx, dy) = cr.text_extents("000 000 000|")

		cr.set_source_rgb(*(col * cfg.intensity_txt for col in cfg.colour))

		cr.set_source_rgb(*(col * cfg.intensity_background for col in cfg.colour))
		if mod.active_track:
			if mod.active_track.trk.index == self.trk.index:
				cr.set_source_rgb(0, 0, 0)
				if mod.record == 1:
					cr.set_source_rgb(*(cfg.record_colour))

		(x, y, width, height, dx, dy) = cr.text_extents("***!")
		self.button_rect.height = self.txt_height * cfg.seq_spacing
		self.button_rect.x = self.trkview.width - (dx + x)
		self.button_rect.y = self.txt_height * cfg.seq_spacing

		(x, y, width, height, dx, dy) = cr.text_extents("***")
		self.button_rect.width = dx + x

		self.popover.set_pointing_to(self.button_rect)

		if self.popped or self.button_highlight:
			cr.set_source_rgb(*(col * cfg.intensity_txt_highlight for col in cfg.star_colour))
		else:
			cr.set_source_rgb(*(col * cfg.intensity_background for col in cfg.colour))

		(x, y, width, height, dx, dy) = cr.text_extents("*** ")

		cr.move_to(self.trkview.width - (dx + x), self.txt_height * 2 * cfg.seq_spacing)
		cr.show_text("***")

		cr.set_line_width((cfg.seq_font_size / 6.0) * cfg.seq_line_width)

		(x, y, width, height, dx, dy) = cr.text_extents("0")
		cr.set_source_rgb(*(col * cfg.intensity_lines for col in cfg.colour))

		cr.move_to(self.width - (width / 2), self.txt_height * cfg.seq_spacing * .3)
		cr.line_to(self.width - (width / 2), 2 * self.txt_height * cfg.seq_spacing)
		cr.stroke()

		# display labels
		cr.set_source_rgb(*(col * cfg.intensity_txt for col in cfg.colour))

		cr.set_source_rgb(*(col * cfg.intensity_background for col in cfg.colour))
		if mod.active_track:
			if mod.active_track.trk.index == self.trk.index:
				cr.set_source_rgb(0, 0, 0)
				if mod.record == 1:
					cr.set_source_rgb(*(cfg.record_colour))

		cr.move_to(x, self.txt_height * .95 *  cfg.seq_spacing)
		if self.trk.name:
			pref = ""
			if not self.trkview.show_notes:
				pref = "p%02dc%02d " % (self.trk.port, self.trk.channel)

			cr.show_text("%s%s" % (pref, self.trk.name))
		else:
			cr.show_text("p%02d c%02d" % (self.trk.port, self.trk.channel))

		self._context.set_font_size(cfg.seq_font_size * .6)
		cr.set_source_rgb(*(col * cfg.intensity_txt_highlight for col in cfg.star_colour))
		yadj = 1.7

		if self.trk.name and self.trkview.show_notes:
			cr.move_to(0, self.txt_height * yadj* cfg.seq_spacing)
			cr.show_text("p%02dc%02d" % (self.trk.port, self.trk.channel))

		if self.trkview.show_pitchwheel and self.trkview.pitchwheel_editor:
			cr.move_to(self.trkview.pitchwheel_editor.x_from, self.txt_height * yadj * cfg.seq_spacing)
			cr.show_text(" pitch")

		if self.trkview.show_controllers:
			for c in self.trkview.controller_editors:
				cr.move_to(c.x_from, self.txt_height * yadj * cfg.seq_spacing)
				cr.show_text(" ctrl %d" % self.trkview.trk.ctrls[c.ctrlnum])

		self.queue_draw()

	def on_enter(self, wdg, prm):
		if self.trk:
			if mod.active_track:
				if not mod.active_track.edit:
					self.seqview.change_active_track(self.seqview.get_track_view(self.trk))

	def on_leave(self, wdg, prm):
		self.button_highlight = False
		self.redraw()

	def on_draw(self, widget, cr):
		cr.set_source_surface(self._surface, 0, 0)
		cr.paint()
		return False

	def tick(self, wdg, param):
		self.redraw()
		return False
