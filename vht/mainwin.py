import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio

from vht import *
from vht.sequenceview import SequenceView

class MainWin(Gtk.ApplicationWindow):
	def __init__(self, app):
		Gtk.ApplicationWindow.__init__(self, application = app)
		self.fs = False
		self.app = app
		mod.mainwin = self
		
		self.last_filename = None		
		
		# fucking gui
		self.hb = Gtk.HeaderBar()
		self.hb.set_show_close_button(True)
		#hb.set_title("")
		#hb.set_subtitle("")
		self.set_titlebar(self.hb)
		
		button = Gtk.Button()
		icon = Gio.ThemedIcon(name="media-playback-stop")
		image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
		button.add(image)
		button.connect("clicked", self.on_stop_button_activate)
		self.hb.pack_start(button)
				
		button = Gtk.Button()
		icon = Gio.ThemedIcon(name="media-playback-start")
		image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
		button.add(image)
		button.connect("clicked", self.on_start_button_activate)
		self.hb.pack_start(button)
		
		label = Gtk.Label("BPM:")
		self.hb.pack_start(label)
		
		self.adj = Gtk.Adjustment(120.0, mod.min_bpm, mod.max_bpm, 1.0, 10.0)
		self.bpmbutton = Gtk.SpinButton()
		self.bpmbutton.set_adjustment(self.adj)
		self.hb.pack_start(self.bpmbutton)
		self.adj.set_value(mod.bpm)
		self.adj.connect("value-changed", self.on_bpm_changed)

		self.time_display = Gtk.Label()
		self.time_display.use_markup = True
		self.hb.pack_end(self.time_display)
		
		self.vbox = Gtk.Box()
		self.hbox = Gtk.Box();

		self.seqlab = Gtk.Label()
		self.seqlab.props.hexpand = False
		
		self.hbox.pack_start(self.seqlab, False, True, 0)

		self._sequence_view = SequenceView(mod[0])
		#self.hbox.pack_start(ModulePropView(self._sequence_view), True, True, 0)
		
		#self.vbox.pack_start(self.hbox, False, False, 0)
		self.vbox.pack_start(self._sequence_view, True, True, 0)
			
		self.vbox.set_orientation(Gtk.Orientation.VERTICAL)
		
		self.add(self.vbox)
		self.set_default_size(800, 600)
		self.show_all()

		if mod.start_error:
			dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR,
				Gtk.ButtonsType.CANCEL, mod.start_error)

			dialog.run()
			dialog.destroy()

		self.add_tick_callback(self.tick)

	def tick(self, wdg, param):
		self.time_display.set_markup("""<span font_desc="Roboto bold" font_family="monospace" size="x-large">%s</span>""" % mod.time)
		return 1

	def on_start_button_activate(self, switch):
		mod.play = 1
		
	def on_stop_button_activate(self, switch):
		if not mod.play:
			mod.reset()
		else:
			pass

		mod.play = False
	
	def on_bpm_changed(self, adj):
		mod.bpm = int(adj.get_value())

	def load(self, filename):
		self._sequence_view.clean()
		mod.load(filename)
		
		self.last_filename = filename
		self.hb.set_title(filename)
		self.adj.set_value(mod.bpm)
		self._sequence_view.seq = mod[0]
		self._sequence_view.build()
