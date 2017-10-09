import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio

from trackerview import TrackerView

class Pms_MainWin(Gtk.ApplicationWindow):
	def __init__(self, pms_handle, app):
		Gtk.ApplicationWindow.__init__(self, application = app)

		print("appinit")
		self.mod = pms_handle
		
		hb = Gtk.HeaderBar()
		hb.set_show_close_button(True)
		hb.props.title = "PMS"
		hb.props.subtitle = "poor man's sequencer"
		self.set_titlebar(hb)
		
		button = Gtk.MenuButton()
		hb.pack_end(button)
		
		self.ptswitch = Gtk.Switch()
		self.ptswitch.set_active(False)
		self.ptswitch.connect("notify::active", self.on_ptswitch_activated)
		
		hb.pack_end(self.ptswitch)
		
		button = Gtk.Button()
		icon = Gio.ThemedIcon(name="media-playback-stop")
		image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
		button.add(image)
		button.connect("clicked", self.on_stop_button_activate)
		hb.pack_start(button)
		
		
		button = Gtk.Button()
		icon = Gio.ThemedIcon(name="media-playback-start")
		image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
		button.add(image)
		button.connect("clicked", self.on_start_button_activate)
		hb.pack_start(button)
		
		label = Gtk.Label("BPM:")
		hb.pack_start(label)
		
		self.adj = Gtk.Adjustment(120.0, 30.0, 400.0, 1.0, 10.0)
		self.bpmbutton = Gtk.SpinButton()
		self.bpmbutton.set_adjustment(self.adj)
		hb.pack_start(self.bpmbutton)
		self.adj.set_value(self.mod.bpm)
		self.adj.connect("value-changed", self.on_bpm_changed)

		self.vbox = Gtk.Box()
		self.hbox = Gtk.Box();

		self.seqlab = Gtk.Label("sequence")
		self.seqlab.props.hexpand = False

		self.hbox.pack_start(self.seqlab, False, True, 0)
		self.hbox.pack_start(Gtk.Label("track props"), True, True, 0)
		
		self.trackerview = TrackerView(self.mod)

		self.vbox.pack_start(self.hbox, False, False, 0)
		self.vbox.pack_start(self.trackerview, True, True, 0)
		self.vbox.set_orientation(Gtk.Orientation.VERTICAL)
		
		self.add(self.vbox)
		self.set_default_size(800, 600)
		self.show_all()

	
	def on_ptswitch_activated(self, switch, gparam):
		self.mod.dump_notes(switch.get_active())

	def on_start_button_activate(self, switch):
		self.mod.playing = 1
		
	def on_stop_button_activate(self, switch):
		if not self.mod.playing:
			self.mod.reset()
		else:
			pass

		self.mod.playing = False
	
	def on_bpm_changed(self, adj):
		self.mod.bpm = int(adj.get_value())
