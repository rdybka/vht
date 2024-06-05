# propview.py - vahatraker
#
# Copyright (C) 2024 Remigiusz Dybka - remigiusz.dybka@gmail.com
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

from vht.trackview import TrackView
from vht.trackpropview import TrackPropView
from vht import *
import cairo
from gi.repository import Gdk, Gtk, Gio
import gi

gi.require_version("Gtk", "3.0")


class PropView(Gtk.ScrolledWindow):
    def __init__(self, seqview):
        Gtk.ScrolledWindow.__init__(self)

        self.connect("scroll-event", self.on_scroll)
        self.connect("draw", self.on_draw)
        self.connect("leave-notify-event", self.on_leave)

        self.seqview = seqview
        self.seq = seqview.seq

        self.last_font_size = self.seqview.font_size

        self._track_box = Gtk.Box()
        self._track_box.set_spacing(0)
        mod.clear_popups = self.clear_popups

        self.set_policy(Gtk.PolicyType.EXTERNAL, Gtk.PolicyType.NEVER)
        self.add_with_viewport(self._track_box)
        self._track_box.show_all()

        self.trk_prop_cache = {}

    def on_scroll(self, widget, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK:  # we're zooming!
            if event.delta_y > 0:
                self.seqview.zoom(-1)

            if event.delta_y < 0:
                self.seqview.zoom(1)

            return True

        return False

    def del_track(self, trk, dest=False):
        track_pv = self._track_box.get_children()[trk.index]
        track_pv.popover.popdown()
        self._track_box.remove(track_pv)
        if dest:
            track_pv.popover.destroy()
            track_pv.destroy()
            del self.trk_prop_cache[int(trk)]

    def on_leave(self, wdg, prm):
        pass

    def add_track(self, trk, trkview):
        if not trk:
            t = TrackPropView(trk, trkview, self.seq, self.seqview, self)
            self._track_box.pack_start(t, False, True, 0)
            t.show()
        else:
            t = None
            if int(trk) in self.trk_prop_cache:
                t = self.trk_prop_cache[int(trk)]
            else:
                t = TrackPropView(trk, trkview, self.seq, self.seqview, self)
                t.show()

            self.trk_prop_cache[int(trk)] = t
            self._track_box.pack_start(t, False, True, 0)

    def move_track(self, trk, offs):
        chld = self._track_box.get_children()
        if trk.index >= len(chld):
            print("gotcha!")
            return
        wdg = chld[trk.index]
        self._track_box.reorder_child(wdg, (trk.index) + offs)
        wdg = self.seqview._track_box.get_children()[trk.index]
        self.seqview._track_box.reorder_child(wdg, (trk.index) + offs)

        self.seq.swap_track(trk.index, trk.index + offs)

    def move_left(self, trk):
        if trk.index == 0:
            return

        self.move_track(trk, -1)

    def move_right(self, trk):
        if trk.index is len(self.seq) - 1:
            return

        self.move_track(trk, 1)

    def move_first(self, trk):
        for i in range(trk.index):
            self.move_track(trk, -1)

    def move_last(self, trk):
        for i in range((len(self.seq) - 1) - trk.index):
            self.move_track(trk, 1)

    def clear_popups(self, ignore=None):
        for wdg in self._track_box.get_children() + [self.seqview._side_prop]:
            if wdg.get_realized():
                if ignore != wdg.popover:
                    wdg.popover.hide()

                    wdg.popped = False
                    wdg.redraw()

        if mod.status_bar.portpopover:
            mod.status_bar.portpopover.hide()
            mod.status_bar.portpopover.pooped = False
        mod.seqlist._popup.hide()
        mod.seqlist._popup.pooped = False
        mod.seqlist.redraw()

    def redraw(self, index=-1):
        for wdg in self._track_box.get_children():
            if wdg.trk.index == index or index == -1:
                wdg.redraw()

        self.queue_draw()

    def on_draw(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        cr.set_source_rgb(*(col * cfg.intensity_background for col in cfg.colour))
        cr.rectangle(0, 0, w, h)
        cr.fill()

        for wdg in self._track_box.get_children():
            if self.last_font_size != self.seqview.font_size:
                wdg.redraw()

        self.last_font_size = self.seqview.font_size
        # super()
