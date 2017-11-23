import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio
import cairo

from vht.trackview import TrackView
from vht.propview import PropView
from vht.trackpropview import TrackPropView
from vht.statusbar import StatusBar

from libvht import mod

class SequenceView(Gtk.Box):
	def __init__(self, seq):
		super(SequenceView, self).__init__()
		
		self._sv = Gtk.ScrolledWindow()
		self._sv.set_events(Gdk.EventMask.POINTER_MOTION_MASK |
			Gdk.EventMask.SCROLL_MASK |
			Gdk.EventMask.ENTER_NOTIFY_MASK |
			Gdk.EventMask.KEY_PRESS_MASK |
			Gdk.EventMask.KEY_RELEASE_MASK)
		
		mod.cfg.on_highlight.append(self.redraw_track)
			
		self._sv.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
		
		self._sv.connect("draw", self.on_draw)
		self._sv.connect("motion-notify-event", self.on_motion)
		self._sv.connect("scroll-event", self.on_scroll)
		self._sv.connect("key-press-event", self.on_key_press)
		self._sv.connect("key-release-event", self.on_key_release)
		self._sv.connect("enter-notify-event", self.on_enter)
		
		self._sv.set_can_focus(True)
		self.add_tick_callback(self.tick)
	
		self.seq = seq;

		self.last_count = len(seq)

		self.def_new_track_width = 0
				
		self._track_box = Gtk.Box()
		self._track_box.set_spacing(0)
		
		self._sv.add_with_viewport(self._track_box)

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
		self._prop_view = PropView(self)
		hbox.pack_end(self._prop_view, True, True, 0)
		
		self._side_prop = TrackPropView(None, self.seq, self, None)
		hbox.pack_start(self._side_prop, False, True, 0)

		self.pack_start(hbox, False, True, 0)
		
		vbox = Gtk.Box()
		vbox.set_orientation(Gtk.Orientation.VERTICAL)
		
		self._status_bar = StatusBar()
				
		hbox = Gtk.Box()
		hbox.pack_start(self._side, False, True, 0)
		hbox.pack_end(self._sv, True, True, 0)

		vbox.pack_start(hbox, True, True, 0)
		vbox.pack_end(self._status_bar, False, True, 0)
				
		self.pack_end(vbox, True, True, 0)
		
		self._sv_vadj = self._sv.get_vadjustment()
		self._sv_hadj = self._sv.get_hadjustment()
		
		self._side_vadj = self._side.get_vadjustment()
		self._prop_view_hadj = self._prop_view.get_hadjustment()
		
		self._sv_vadj.connect("value-changed", self.on_sv_vadj_changed)
		self._side_vadj.connect("value-changed", self.on_sv_vadj_changed)
		
		self._sv_hadj.connect("value-changed", self.on_sv_hadj_changed)
		self._prop_view_hadj.connect("value-changed", self.on_sv_hadj_changed)
					
		self.add_track(None)
		self.build()

		self.show_all()

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
			dest_adj = self._prop_view_hadj
		else:
			dest_adj = self._sv_hadj

		dest_adj.set_upper(adj.get_upper())
		dest_adj.set_value(adj.get_value())

	def on_key_press(self, widget, event):
		#print(event.keyval, event.state)
	
		if event.keyval == 65293:		# enter
			if event.state & Gdk.ModifierType.MOD1_MASK: # alt-enter
				if mod.mainwin.fs:
					mod.mainwin.unfullscreen()
					mod.mainwin.fs = False
				else:
					mod.mainwin.fullscreen()
					mod.mainwin.fs = True
			
				return True
			
			# play/stop
			if mod.play:
				mod.play = 0
			else:
				mod.play = 1
			
		if event.keyval == 65307:			# esc
			if mod.active_track:
				if mod.active_track.edit:
					return mod.active_track.on_key_press(widget, event)
			
			if not mod.play:
				mod.reset()
				
			return True
	
		if event.keyval == 122:			# z
			if event.state & Gdk.ModifierType.CONTROL_MASK:
				if mod.active_track:
					return mod.active_track.on_key_press(widget, event)
				
		if event.keyval == 65451:		# +
			if event.state & Gdk.ModifierType.CONTROL_MASK:
				self.zoom(1)
				return True

		if event.keyval == 65451:		# +
			mod.cfg.skip += 1
			return True
		
		if event.keyval == 65453:		# -
			if event.state & Gdk.ModifierType.CONTROL_MASK:
				self.zoom(-1)
				return True
				
		if event.keyval == 65453:		# -
			mod.cfg.skip -= 1
			return True
		
		if event.keyval == 113:		# q
			if event.state & Gdk.ModifierType.CONTROL_MASK:
				mod.mainwin.close()
				return True
		
		if event.keyval == 65450:		# *
			mod.cfg.octave += 1
			if mod.cfg.octave > 8:
				mod.cfg.octave = 8
			
			return True
		
		if event.keyval == 65455:		# /
			mod.cfg.octave -= 1
			if mod.cfg.octave < 0:
				mod.cfg.octave = 0
			return True
		
		if not mod.active_track:
			vals = [65364, 65362, 65363, 65361, 65366, 65365, 65360, 65367]
				
			for v in vals:
				if event.keyval == v:
					mod.active_track = self.get_tracks()[0]
					if not mod.active_track.select_start:
						mod.active_track.edit = 0, 0
						mod.active_track.redraw(0)
						return True
					
		if mod.active_track:
			if not mod.active_track.edit:
				vals = [65364, 65362, 65363, 65361, 65366, 65365, 65360, 65367]
			
				for v in vals:
					if event.keyval == v:
						if not mod.active_track.select_start:
							mod.active_track.edit = 0, 0
							mod.active_track.redraw(0)
							return True
			
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
		mod.cfg.seq_font_size += i 
			
		if mod.cfg.seq_font_size < 1:
			mod.cfg.seq_font_size = 1

		mod.cfg.pointer_height = .7 * mod.cfg.seq_font_size
		self.redraw_track(None)
		self._side_prop.redraw()
		self._prop_view.redraw()
	
	def on_scroll(self, widget, event):
		if event.state & Gdk.ModifierType.CONTROL_MASK: # we're zooming!
			if event.delta_y > 0:
				self.zoom(-1)
			
			if event.delta_y < 0:
				self.zoom(1)
			
			return True
			
		if mod.active_track:
			if mod.active_track.edit:
				old = mod.active_track.edit[1]

				mod.active_track.edit = int(mod.active_track.edit[0]), int(mod.active_track.edit[1] + event.delta_y)
				
				if mod.active_track.edit[1] >= mod.active_track.trk.nrows:
					mod.active_track.edit = mod.active_track.edit[0], mod.active_track.trk.nrows - 1
				
				if mod.active_track.edit[1] < 0:
					mod.active_track.edit = mod.active_track.edit[0], 0
				
				mod.active_track.redraw(old)
				mod.active_track.redraw(mod.active_track.edit[1])
				return True	
			
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
			self._prop_view.add_track(trk)
		
		t.show()

	def del_track(self, trk):
		for wdg in self.get_tracks():
			if wdg.trk.index == trk.index:
				TrackView.track_views.remove(wdg)
				self.seq.del_track(trk.index)
				wdg.destroy()
				self.recalculate_row_spacing()
				return
	
	def change_active_track(self, trk):
		ac = mod.active_track
		
		mod.active_track = trk
		if ac != trk:
			if ac:
				self._prop_view.redraw(ac.trk.index)
			self._prop_view.redraw(trk.trk.index)
	
	def redraw_track(self, trk = None):
		for wdg in self.get_tracks(True):
			rdr = False
			if not trk:
				rdr = True
			else:
				if wdg.trk:
					if wdg.trk.index == trk.index:
						rdr = True	 
			if rdr:
				wdg.redraw()

		self.queue_draw()
			
	def build(self):
		for trk in self.seq:
			self.add_track(trk)
	
	def recalculate_row_spacing(self):
		minspc = 1.0
		
		for wdg in self.get_tracks(True):
			if wdg.trk == None:
				spc = 1.0
			else:
				spc = wdg.trk.nsrows / wdg.trk.nrows
			wdg.spacing = spc

			if spc < minspc:
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
		
		vtarget = (trk.edit[1] * trk.txt_height) + trk.txt_height / 2.0
		trk_height = trk.txt_height * trk.trk.nrows
		vtarget = vtarget - (h / 2.0)
				
		if vtarget < 0:
			vtarget = 0
		
		if vtarget > trk_height - h:
			vtarget = trk_height - h
		
		vtarget = vadj.get_value() + ((vtarget - vadj.get_value()) * mod.cfg.auto_scroll_delay)
		
		vadj.set_value(vtarget)
		
		htarget = (trk.edit[0] * trk.txt_width) + trk.txt_width / 2.0
		for wdg in self.get_tracks()[:trk.trk.index]:
			htarget += wdg.txt_width * len(wdg.trk)
	
		trk_width = trk.txt_width * len(trk.trk)
		htarget = htarget - (w / 2.0)
				
		if htarget < 0:
			htarget = 0

		if htarget > self._track_box.get_allocated_width() - w:
			htarget = self._track_box.get_allocated_width() - w
		
		htarget = hadj.get_value() + ((htarget - hadj.get_value()) * mod.cfg.auto_scroll_delay)

		hadj.set_value(htarget)
		
		self._sv.set_hadjustment(hadj)
		self._sv.set_vadjustment(vadj)
	
	def tick(self, wdg, param):
		for wdg in self.get_tracks(True):
				wdg.tick()
				if wdg.edit and wdg.trk:
					self.auto_scroll(wdg)
		return 1
	
	def on_draw(self, widget, cr):
		w = widget.get_allocated_width()
		h = widget.get_allocated_height()
		
		cr.set_source_rgb(*(col * mod.cfg.intensity_background for col in mod.cfg.colour))
		cr.rectangle(0, 0, w, h)
		cr.fill()

	def get_tracks(self, with_side_view = False):
		ret = []
		for wdg in self._track_box.get_children():
			ret.append(wdg)

		if with_side_view:
			ret.append(self._side_box.get_children()[0])

		return ret
	
	def on_enter(self, wdg, prm):
		self._sv.grab_focus()
