import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio
import cairo

class SequencePropViewPopover(Gtk.Popover):
	def __init__(self, parent, seq):
		super(Gtk.Popover, self).__init__()
		self.set_relative_to(parent)

		self.set_events(Gdk.EventMask.LEAVE_NOTIFY_MASK | Gdk.EventMask.ENTER_NOTIFY_MASK)
		self.connect("leave-notify-event", self.on_leave)
		self.connect("enter-notify-event", self.on_enter)
		self.entered = False
		
		self.parent = parent
		self.seq = seq
		self.grid = Gtk.Grid()
		self.grid.set_column_spacing(3)
		self.grid.set_row_spacing(3)

		button = Gtk.Button()
		icon = Gio.ThemedIcon(name="list-add")
		image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
		button.add(image)
		button.connect("clicked", self.on_add_button_clicked)
		button.set_tooltip_text("CTRL + T")
		self.grid.attach(button, 0, 0, 1, 1)

		self.length_adj = Gtk.Adjustment(0, 0, 256, 1.0, 1.0)
		self.length_button = Gtk.SpinButton()
		self.length_button.set_adjustment(self.length_adj)
		self.length_adj.set_value(seq.length)
		self.length_adj.connect("value-changed", self.on_length_changed)

		self.grid.attach(self.length_button, 0, 1, 1, 1)
		
		self.grid.show_all()
		self.add(self.grid)

	def on_length_changed(self, adj):
		self.seq.length = int(adj.get_value())
		self.parent.seqview.recalculate_row_spacing()
		self.parent.seqview.redraw_track()
		self.parent.seqview.queue_draw()

	def on_leave(self, wdg, prm):
		if prm.detail == Gdk.NotifyType.NONLINEAR:
			wdg.popdown()
			self.entered = False

	def on_enter(self, wdg, prm):
		if prm.detail == Gdk.NotifyType.NONLINEAR:
			if self.entered == 0:
				self.entered = True

	def on_add_button_clicked(self, switch):
		self.parent.add_track()
	
