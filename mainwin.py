import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio

from sequenceview import SequenceView
from propview import PropView

from pypms import pms

class MainWin(Gtk.ApplicationWindow):
	def __init__(self, app):
		Gtk.ApplicationWindow.__init__(self, application = app)
		self.pms = pms

		# fucking gui
		hb = Gtk.HeaderBar()
		hb.set_show_close_button(True)
		hb.props.title = "PMS"
		hb.props.subtitle = "poor man's sequencer"
		self.set_titlebar(hb)
		
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
		self.adj.set_value(pms.bpm)
		self.adj.connect("value-changed", self.on_bpm_changed)

		self.time_display = Gtk.Label()
		self.time_display.use_markup = True
		hb.pack_end(self.time_display)
		
		self.vbox = Gtk.Box()
		self.hbox = Gtk.Box();

		self.seqlab = Gtk.Label("sequence")
		self.seqlab.props.hexpand = False
		
		self.hbox.pack_start(self.seqlab, False, True, 0)
		self.hbox.pack_start(Gtk.Label("track props"), True, True, 0)
		
		self._sequence_view = SequenceView(pms[0])
		self._prop_view = PropView(self._sequence_view)

		self._seq_scroll = Gtk.ScrolledWindow()
		self._seq_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
		sb = Gtk.Box()
		sb.set_orientation(Gtk.Orientation.VERTICAL)
		sb.pack_start(self._prop_view, False, True, 0)
		sb.pack_start(self._sequence_view, True, True, 0)
		self._seq_scroll.add_with_viewport(sb)

		self.vbox.pack_start(self.hbox, False, False, 0)
		self.vbox.pack_start(self._seq_scroll, True, True, 0)
		self.vbox.set_orientation(Gtk.Orientation.VERTICAL)
		
		self.add(self.vbox)
		self.set_default_size(800, 600)
		self.show_all()

		if pms.start_error:
			dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR,
				Gtk.ButtonsType.CANCEL, pms,start_error)

			dialog.run()
			dialog.destroy()

		self.add_tick_callback(self.tick)
	
	def tick(self, wdg, param):
		self.time_display.set_markup("""<span font_desc="Roboto bold" font_family="monospace" foreground="black" size="x-large">%s</span>""" % self.pms.time)
		self.time_display.queue_draw()
		return 1

	def on_start_button_activate(self, switch):
		pms.play = 1
		
	def on_stop_button_activate(self, switch):
		if not pms.play:
			pms.reset()
		else:
			pass

		pms.play = False
	
	def on_bpm_changed(self, adj):
		pms.bpm = int(adj.get_value())
