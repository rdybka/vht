import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gdk, Gtk, Gio
import cairo

from vht import *

class SequencePropViewPopover(Gtk.Popover):
	def __init__(self, parent, seq):
		super(SequencePropViewPopover, self).__init__()
		self.set_relative_to(parent)

		self.set_events(Gdk.EventMask.LEAVE_NOTIFY_MASK
			| Gdk.EventMask.ENTER_NOTIFY_MASK)

		self.connect("leave-notify-event", self.on_leave)
		self.connect("enter-notify-event", self.on_enter)

		self.parent = parent
		self.seq = seq
		self.grid = Gtk.Grid()
		self.grid.set_column_spacing(3)
		self.grid.set_row_spacing(3)

		self.entered = False

		button = Gtk.Button()
		icon = Gio.ThemedIcon(name="list-add")
		image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
		button.add(image)
		button.connect("clicked", self.on_add_button_clicked)
		button.set_tooltip_markup(cfg.tooltip_markup % (cfg.key["track_add"]))
		self.grid.attach(button, 0, 0, 1, 1)

		self.length_adj = Gtk.Adjustment(0, 0, 256, 1.0, 1.0)
		self.length_button = Gtk.SpinButton()
		self.length_button.set_adjustment(self.length_adj)
		self.length_adj.set_value(seq.length)
		self.length_adj.connect("value-changed", self.on_length_changed)

		self.grid.attach(self.length_button, 0, 1, 1, 1)

		self.grid.show_all()
		self.add(self.grid)
		self.set_modal(False)

	def on_length_changed(self, adj):
		self.seq.length = int(adj.get_value())
		for trk in self.seq:
			if trk.nsrows > self.seq.length:
				trk.nsrows  = self.seq.length

		self.parent.seqview.recalculate_row_spacing()
		self.parent.seqview.redraw_track()
		self.parent.seqview.queue_draw()

	def on_leave(self, wdg, prm):
		if not self.entered:
			return True

		if prm.window == self.get_window():
			if prm.detail != Gdk.NotifyType.INFERIOR:
				self.unpop()
				return True

		return True

	def on_enter(self, wdg, prm):
		if prm.window == self.get_window():
			if prm.detail == Gdk.NotifyType.INFERIOR:
				self.entered = True

		return True

	def unpop(self):
		self.popdown()
		self.entered = False
		self.parent.popped = False
		self.parent.button_highlight = False
		self.parent.redraw()

	def on_add_button_clicked(self, switch):
		self.parent.add_track()
		self.parent.seqview.recalculate_row_spacing()

	def pop(self):
		mod.clear_popups(self)
		self.popup()
		self.entered = False
