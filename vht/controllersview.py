import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio

from vht import cfg, mod
from vht.controllersviewrow import ControllersViewRow
from vht.controllereditor import ControllerEditor

class ControllersView(Gtk.Box):
	def __init__(self, trk, trkview, parent):
		super(ControllersView, self).__init__()

		self.set_orientation(Gtk.Orientation.VERTICAL)

		self.sw = Gtk.ScrolledWindow()

		self.parent = parent
		self.trk = trk
		self.trkview = trkview
		self.capturing = False

		self.box = Gtk.Box()
		self.box.set_orientation(Gtk.Orientation.VERTICAL)
		self.box.set_homogeneous(False)
		self.box.set_spacing(2)

		self.sw.add(self.box)
		self.pack_start(self.sw, True, True, 0)

		self.new_ctrl = Gtk.ActionBar()

		button = Gtk.Button()
		icon = Gio.ThemedIcon(name="edit-add")
		image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
		button.add(image)
		button.connect("clicked", self.on_add_clicked)
		self.new_ctrl.pack_start(button)

		self.capture_button = Gtk.ToggleButton()
		self.capture_button.set_tooltip_markup(cfg.tooltip_markup % ("capture"))
		icon = Gio.ThemedIcon(name="media-record")
		image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
		self.capture_button.add(image)
		self.capture_button.connect("toggled", self.on_capture_toggled)
		self.new_ctrl.pack_start(self.capture_button)

		self.new_ctrl_adj = Gtk.Adjustment(1, 1, 127, 1.0, 1.0)
		self.new_ctrl_button = Gtk.SpinButton()
		self.new_ctrl_button.set_adjustment(self.new_ctrl_adj)
		self.new_ctrl_adj.set_value(1)
		self.new_ctrl.pack_start(self.new_ctrl_button)

		self.pack_end(self.new_ctrl, False, False, 0)
		self.rebuild()
		self.show_all()

	def on_capture_toggled(self, wdg):
		if wdg.get_active():
			mod.gui_midi_capture = True
			self.capturing = True
			self.add_tick_callback(self.tick)
		else:
			self.capturing = False
			mod.gui_midi_capture = False

	def tick(self, wdg, param):
		if not self.capturing:
			self.capture_button.set_active(False)
			return False

		midin = mod.get_midi_in_event()

		while midin:
			if midin["type"] == 4:
				self.new_ctrl_adj.set_value(midin["note"])
			midin = mod.get_midi_in_event()

		return True

	def rebuild(self, just_gui = False):
		reuse = False

		if len(self.box.get_children()) == self.trk.nctrl - 1:
			reuse = True

		if not reuse:
			for wdg in self.box.get_children():
				self.box.remove(wdg)

		for i, c in enumerate(self.trk.ctrls):
			if c != -1:
				if not reuse:
					rw = ControllersViewRow(self, self.trk, c, i)
					self.box.pack_start(rw, False, False, 0)
				else:
					rw = self.box.get_children()[i - 1]
					rw.ctrlnum = c
					rw.ctrl_adj.set_value(c)

		for i, w in enumerate(self.box.get_children()):
			w.up_button.set_sensitive(True)
			w.down_button.set_sensitive(True)

			if i == 0:
				w.up_button.set_sensitive(False)

			if i == self.trk.nctrl - 2:
				w.down_button.set_sensitive(False)

		self.parent.refresh()

		if not just_gui:
			self.trkview.redraw_full()

		if self.get_realized():
			self.parent.parent.redraw()

	def on_add_clicked(self, wdg):
		self.trk.ctrl.add(int(self.new_ctrl_adj.get_value()))
		self.trkview.controller_editors.append(ControllerEditor(self.trkview, len(self.trk.ctrl) - 1))
		self.trkview.show_controllers = True
		self.rebuild()
