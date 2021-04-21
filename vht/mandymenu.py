# mandymenu.py - Valhalla Tracker
#
# Copyright (C) 2021 Remigiusz Dybka - remigiusz.dybka@gmail.com
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

import math
import cairo
import gi
import os
import random

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Gio

from vht import cfg, mod


def add_scale(parent, x, i, m, t, label, callback):
    ret = Gtk.Scale.new_with_range(Gtk.Orientation.VERTICAL, i, m, t)

    ret.set_draw_value(False)
    ret.set_inverted(True)
    ret.set_vexpand(True)

    # ret.set_orientation(Gtk.Orientation.VERTICAL)
    ret.connect("value-changed", callback)

    parent.attach(ret, x, 1, 1, 1)
    retlab = Gtk.Label()
    parent.attach(retlab, x, 0, 1, 1)
    parent.attach(Gtk.Label.new(label), x, 2, 1, 1)

    return ret, retlab


class MandyMenu(Gtk.Box):
    def __init__(self, mandy):
        super(MandyMenu, self).__init__()

        self.mandy = mandy

        self.frozen = False

        self.set_orientation(Gtk.Orientation.VERTICAL)

        self.buttgrid = Gtk.Grid()

        # active / running / direction
        self.butt_active = Gtk.ToggleButton()
        icon = Gio.ThemedIcon(name="media-playback-start")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.butt_active.add(image)
        self.butt_active.set_tooltip_markup(
            cfg.tooltip_markup2 % ("active", cfg.key["mandy_active"])
        )
        self.butt_active.connect("toggled", self.on_active_toggled, 0)

        self.butt_pause = Gtk.ToggleButton()
        icon = Gio.ThemedIcon(name="media-playback-pause")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.butt_pause.add(image)
        self.butt_pause.set_tooltip_markup(
            cfg.tooltip_markup2 % ("pause", cfg.key["mandy_pause"])
        )
        self.butt_pause.connect("toggled", self.on_pause_toggled, 0)

        self.butt_dir = Gtk.Button()

        icon = Gio.ThemedIcon(name="media-seek-backward")
        self.left_image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)

        icon = Gio.ThemedIcon(name="media-seek-forward")
        self.right_image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)

        self.butt_dir.set_image(self.left_image)
        self.butt_dir.connect("clicked", self.on_dir_clicked, 0)
        self.butt_dir.set_tooltip_markup(
            cfg.tooltip_markup2 % ("direction", cfg.key["mandy_direction"])
        )

        self.buttgrid.attach(self.butt_active, 0, 0, 1, 1)
        self.buttgrid.attach(self.butt_pause, 1, 0, 1, 1)
        self.buttgrid.attach(self.butt_dir, 2, 0, 1, 1)

        # follow
        self.butt_follow = Gtk.ToggleButton()
        self.butt_follow.connect("toggled", self.on_follow_toggled, 0)

        icon = Gio.ThemedIcon(name="zoom-fit-best")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.butt_follow.add(image)
        self.butt_follow.set_tooltip_markup(
            cfg.tooltip_markup2 % ("follow", cfg.key["mandy_next"])
        )
        self.buttgrid.attach(self.butt_follow, 0, 1, 1, 1)

        # reset
        self.butt_reset = Gtk.Button.new_with_label("///")
        self.butt_reset.connect("clicked", self.on_reset_clicked, 0)
        self.butt_reset.set_tooltip_markup(cfg.tooltip_markup % ("reset"))
        self.buttgrid.attach(self.butt_reset, 1, 1, 1, 1)

        # mnd/jul
        self.butt_jmode = Gtk.ToggleButton.new_with_label("jul")
        self.butt_jmode.connect("toggled", self.on_jmode_toggled, 0)
        self.butt_jmode.set_tooltip_markup(
            cfg.tooltip_markup2 % ("fractal type", "mandelbrot / julia")
        )
        self.buttgrid.attach(self.butt_jmode, 2, 1, 1, 1)

        self.pack_start(self.buttgrid, False, False, 0)

        self.scrlwin = Gtk.ScrolledWindow(None, None)
        self.scrlwin.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        self.scrlwin.set_overlay_scrolling(False)

        self.pack_end(self.scrlwin, True, True, 0)

        self.details = Gtk.Box.new(Gtk.Orientation.VERTICAL, 1)
        self.details.set_vexpand(True)

        self.det1 = Gtk.Grid()
        # self.det1.set_column_homogeneous(True)
        self.det1.set_column_spacing(5)

        # miter
        self.scale_miter, self.lab_itr = add_scale(
            self.det1, 0, 2, mandy.max_iter, 1, "itr", self.on_miter_changed
        )
        self.scale_miter.set_tooltip_markup(
            cfg.tooltip_markup2 % ("iterations", "ctrl-scroll")
        )

        # quantise
        self.scale_qnt, self.lab_qnt = add_scale(
            self.det1, 1, 0, 8, 1, "qnt", self.on_qnt_changed
        )

        self.scale_qnt.set_tooltip_markup(cfg.tooltip_markup % ("quantise to nth-row"))

        # speed
        self.scale_speed, self.lab_spd = add_scale(
            self.det1, 2, 0.1, self.mandy.max_speed, 0.1, "spd", self.on_speed_changed
        )
        self.scale_speed.set_tooltip_markup(
            cfg.tooltip_markup2 % ("speed", "shift-scroll")
        )

        # phase
        self.scale_phase, self.lab_phs = add_scale(
            self.det1, 3, -180, 180, 0.1, "phs", self.on_phase_changed
        )

        self.scale_phase.add_mark(0, Gtk.PositionType.TOP, None)
        self.scale_phase.set_digits(1)
        self.scale_phase.set_tooltip_markup(cfg.tooltip_markup % ("phase"))

        # mult
        self.scale_mult, self.lab_mlt = add_scale(
            self.det1, 4, 0.1, 5, 0.1, "mlt", self.on_mult_changed
        )

        self.scale_mult.add_mark(1, Gtk.PositionType.TOP, None)
        self.scale_mult.set_digits(1)
        self.scale_mult.set_tooltip_markup(cfg.tooltip_markup % ("angle multiplier"))

        # julias
        self.scale_jvx, self.lab_jvx = add_scale(
            self.det1, 5, 0, 100, 0.1, "jvx", self.on_jvx_changed
        )
        self.scale_jvx.set_tooltip_markup(
            cfg.tooltip_markup % ("julia (e) LFO x velocity")
        )

        self.scale_jvy, self.lab_jvy = add_scale(
            self.det1, 6, 0, 100, 0.1, "jvy", self.on_jvy_changed
        )
        self.scale_jvy.set_tooltip_markup(
            cfg.tooltip_markup % ("julia (e) LFO y velocity")
        )

        self.scale_jsx, self.lab_jsx = add_scale(
            self.det1, 7, 0, 100, 0.1, "jsx", self.on_jsx_changed
        )
        self.scale_jsx.set_tooltip_markup(
            cfg.tooltip_markup % ("julia (e) LFO x speed")
        )

        self.scale_jsy, self.lab_jsy = add_scale(
            self.det1, 8, 0, 100, 0.1, "jsy", self.on_jsy_changed
        )
        self.scale_jsy.set_tooltip_markup(
            cfg.tooltip_markup % ("julia (e) LFO y speed")
        )

        self.details.pack_start(self.det1, True, True, 0)

        self.scrlwin.add_with_viewport(self.details)

        self.update()

        self.show_all()

    def update(self):
        self.frozen = True
        fr = False
        if self.get_window():
            self.get_window().freeze_updates()
            fr = True

        self.butt_active.set_active(True if self.mandy.active else False)
        self.butt_pause.set_active(True if self.mandy.pause else False)
        self.butt_jmode.set_active(self.mandy.julia)

        if self.mandy.active:
            self.butt_pause.set_sensitive(True)
            self.butt_dir.set_sensitive(True)
            self.butt_follow.set_sensitive(True)
            self.scale_qnt.set_sensitive(True)
            self.scale_speed.set_sensitive(True)
            self.scale_mult.set_sensitive(True)
            self.scale_phase.set_sensitive(True)
            self.scale_jvx.set_sensitive(True)
            self.scale_jvy.set_sensitive(True)
            self.scale_jsx.set_sensitive(True)
            self.scale_jsy.set_sensitive(True)
        else:
            self.butt_pause.set_sensitive(False)
            self.butt_dir.set_sensitive(False)
            self.scale_qnt.set_sensitive(False)
            self.butt_follow.set_sensitive(False)
            self.scale_speed.set_sensitive(False)
            self.scale_mult.set_sensitive(False)
            self.scale_phase.set_sensitive(False)
            self.scale_jvx.set_sensitive(False)
            self.scale_jvy.set_sensitive(False)
            self.scale_jsx.set_sensitive(False)
            self.scale_jsy.set_sensitive(False)

        if len(self.mandy):
            if self.mandy[0].speed > 0:
                self.butt_dir.set_image(self.left_image)
            else:
                self.butt_dir.set_image(self.right_image)

            self.butt_follow.set_active(True if self.mandy.follow > -1 else False)
            self.lab_qnt.set_text("%d" % self.mandy[0].qnt)
            self.scale_qnt.set_value(self.mandy[0].qnt)
            self.lab_itr.set_text("%d" % self.mandy.miter)
            self.scale_miter.set_value(self.mandy.miter)
            self.lab_spd.set_text("%.1f" % self.mandy[0].speed)
            self.scale_speed.set_value(abs(self.mandy[0].speed))
            self.lab_phs.set_text("%.1f" % self.mandy[0].phase)
            self.scale_phase.set_value(self.mandy[0].phase)
            self.lab_mlt.set_text("%.1f" % self.mandy[0].mult)
            self.scale_mult.set_value(self.mandy[0].mult)

            self.lab_jvx.set_text("%.1f" % self.mandy.jvx)
            self.scale_jvx.set_value(self.mandy.jvx)

            self.lab_jvy.set_text("%.1f" % self.mandy.jvy)
            self.scale_jvy.set_value(self.mandy.jvy)

            self.lab_jsx.set_text("%.1f" % self.mandy.jsx)
            self.scale_jsx.set_value(self.mandy.jsx)

            self.lab_jsy.set_text("%.1f" % self.mandy.jsy)
            self.scale_jsy.set_value(self.mandy.jsy)

        if fr:
            self.get_window().thaw_updates()

        self.frozen = False

    def on_active_toggled(self, wdg, param):
        if self.frozen:
            return

        if wdg.get_active():
            self.mandy.active = True
        else:
            self.mandy.active = False

        self.update()

    def on_pause_toggled(self, wdg, param):
        if self.frozen:
            return

        if wdg.get_active():
            self.mandy.pause = True
        else:
            self.mandy.pause = False

    def on_dir_clicked(self, wdg, param):
        if self.frozen:
            return

        self.mandy[0].speed *= -1
        self.update()

    def on_reset_clicked(self, wdg, param):
        if self.frozen:
            return

        self.mandy.zoom = 6
        self.mandy.rot = 0
        self.mandy.set_xy(-0.7, 0)
        self.mandy.set_jxy(0.0, 0)

    def on_jmode_toggled(self, wdg, param):
        if self.frozen:
            return

        self.mandy.julia = wdg.get_active()
        self.update()

    def on_follow_toggled(self, wdg, param):
        if self.frozen:
            return

        if wdg.get_active():
            self.mandy.follow = 0
        else:
            self.mandy.follow = -1

    def on_qnt_changed(self, adj):
        if self.frozen:
            return

        self.mandy[0].qnt = int(adj.get_value())
        self.update()

    def on_miter_changed(self, adj):
        if self.frozen:
            return

        self.mandy.miter = int(adj.get_value())
        self.update()

    def on_speed_changed(self, adj):
        if self.frozen:
            return

        s = adj.get_value()

        self.mandy[0].speed = s if self.mandy[0].speed > 0 else -s
        self.update()

    def on_phase_changed(self, adj):
        if self.frozen:
            return

        self.mandy[0].phase = adj.get_value()
        self.update()

    def on_mult_changed(self, adj):
        if self.frozen:
            return

        self.mandy[0].mult = adj.get_value()
        self.update()

    def on_jvx_changed(self, adj):
        if self.frozen:
            return

        self.mandy.jvx = adj.get_value()
        self.update()

    def on_jvy_changed(self, adj):
        if self.frozen:
            return

        self.mandy.jvy = adj.get_value()
        self.update()

    def on_jsx_changed(self, adj):
        if self.frozen:
            return

        self.mandy.jsx = adj.get_value()
        self.update()

    def on_jsy_changed(self, adj):
        if self.frozen:
            return

        self.mandy.jsy = adj.get_value()
        self.update()

    def on_jvy_changed(self, adj):
        if self.frozen:
            return

        self.mandy.jvy = adj.get_value()
        self.update()

    def on_jsx_changed(self, adj):
        if self.frozen:
            return

        self.mandy.jsx = adj.get_value()
        self.update()

    def on_jsy_changed(self, adj):
        if self.frozen:
            return

        self.mandy.jsy = adj.get_value()
        self.update()
