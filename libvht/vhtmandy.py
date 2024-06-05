# vhtmandy.py - vahatraker (libvht)
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

from collections.abc import Iterable

from libvht import libcvht
from libvht.vhttracy import VHTTracy


class VHTMandy(Iterable):
    def __init__(self, mnd, trk):
        super(VHTMandy, self).__init__()
        self._trk_handle = trk
        self._mnd_handle = mnd
        self._npoints = 0

    def __len__(self):
        return libcvht.mandy_get_ntracies(self._mnd_handle)

    def __iter__(self):
        for itm in range(self.__len__()):
            yield VHTTracy(libcvht.mandy_get_tracy(self._mnd_handle, itm))

    def __getitem__(self, itm):
        if itm >= self.__len__():
            return None

        if itm < 0:
            if not len(self) >= -itm:
                raise IndexError()

        return VHTTracy(libcvht.mandy_get_tracy(self._mnd_handle, itm))

    def get_pixels(self, w, h, stride):
        return libcvht.mandy_get_pixels(self._mnd_handle, int(w), int(h), stride)

    def get_points(self):
        pts = libcvht.double_array(self._npoints)
        libcvht.mandy_get_points(self._mnd_handle, pts, self._npoints)
        return pts

    def set_rgb(self, r, g, b):
        libcvht.mandy_set_rgb(self._mnd_handle, int(r), int(g), int(b))

    def set_xy(self, x, y):
        libcvht.mandy_set_xy(self._mnd_handle, float(x), float(y))

    def set_jxy(self, jx, jy):
        libcvht.mandy_set_jxy(self._mnd_handle, float(jx), float(jy))

    def render(self, w, h):  # to return pointlist (length)
        self._npoints = libcvht.mandy_render(self._mnd_handle, int(w), int(h))
        return self._npoints

    def set_cxy(self, x, y):
        libcvht.mandy_set_cxy(self._mnd_handle, float(x), float(y))

    def screen_translate(self, x, y, w, h):
        libcvht.mandy_translate(
            self._mnd_handle, float(x), float(y), float(w), float(h)
        )

    def julia_translate(self, x, y, w, h):
        libcvht.mandy_translate_julia(
            self._mnd_handle, float(x), float(y), float(w), float(h)
        )

    def screen_rotate(self, x, y, w, h):
        libcvht.mandy_rotate(self._mnd_handle, float(x), float(y), float(w), float(h))

    def screen_zoom(self, x, y, w, h):
        libcvht.mandy_zoom(self._mnd_handle, float(x), float(y), float(w), float(h))

    def reinit_from_scan(self):
        libcvht.mandy_reinit_from_scan(self._mnd_handle)

    def reset_anim(self):
        libcvht.mandy_reset_anim(self._mnd_handle)

    def reset(self):
        libcvht.mandy_reset(self._mnd_handle)

    @property
    def scan_tracy(self):
        trc_h = libcvht.mandy_get_scan_tracy(self._mnd_handle)
        if trc_h:
            return VHTTracy(trc_h)
        else:
            return None

    @property
    def init_tracy(self):
        trc_h = libcvht.mandy_get_init_tracy(self._mnd_handle)
        if trc_h:
            return VHTTracy(trc_h)
        else:
            return None

    @property
    def pause(self):
        ret = libcvht.mandy_get_pause(self._mnd_handle)
        return True if ret else False

    @pause.setter
    def pause(self, val):
        libcvht.mandy_set_pause(self._mnd_handle, 1 if val else 0)

    def step(self):
        libcvht.mandy_step(self._mnd_handle)

    @property
    def active(self):
        return libcvht.mandy_get_active(self._mnd_handle)

    @active.setter
    def active(self, active):
        return libcvht.mandy_set_active(self._mnd_handle, int(active))

    @property
    def zoom(self):
        return libcvht.mandy_get_zoom(self._mnd_handle)

    @zoom.setter
    def zoom(self, zoom):
        libcvht.mandy_set_zoom(self._mnd_handle, float(zoom))

    @property
    def rot(self):
        return libcvht.mandy_get_rot(self._mnd_handle)

    @rot.setter
    def rot(self, rot):
        libcvht.mandy_set_rot(self._mnd_handle, float(rot))

    @property
    def save_state(self):
        return libcvht.mandy_save(self._mnd_handle)

    def init_from(self, state):
        libcvht.mandy_restore(self._mnd_handle, state)

    @property
    def jsx(self):
        return libcvht.mandy_get_jsx(self._mnd_handle)

    @jsx.setter
    def jsx(self, jsx):
        libcvht.mandy_set_jsx(self._mnd_handle, float(jsx))

    @property
    def jsy(self):
        return libcvht.mandy_get_jsy(self._mnd_handle)

    @jsy.setter
    def jsy(self, jsy):
        libcvht.mandy_set_jsy(self._mnd_handle, float(jsy))

    @property
    def jvx(self):
        return libcvht.mandy_get_jvx(self._mnd_handle)

    @jvx.setter
    def jvx(self, jvx):
        libcvht.mandy_set_jvx(self._mnd_handle, float(jvx))

    @property
    def jvy(self):
        return libcvht.mandy_get_jvy(self._mnd_handle)

    @jvy.setter
    def jvy(self, jvy):
        libcvht.mandy_set_jvy(self._mnd_handle, float(jvy))

    @property
    def bail(self):
        return libcvht.mandy_get_bail(self._mnd_handle)

    @bail.setter
    def bail(self, bail):
        libcvht.mandy_set_bail(self._mnd_handle, float(bail))

    @property
    def miter(self):
        return libcvht.mandy_get_miter(self._mnd_handle)

    @miter.setter
    def miter(self, miter):
        libcvht.mandy_set_miter(self._mnd_handle, int(miter))

    @property
    def max_iter(self):
        return libcvht.mandy_get_max_iter(self._mnd_handle)

    @property
    def max_speed(self):
        return libcvht.mandy_get_max_speed()

    @property
    def info(self):
        ret = libcvht.mandy_get_info(self._mnd_handle)
        return ret if len(ret) else None

    @property
    def follow(self):
        return libcvht.mandy_get_follow(self._mnd_handle)

    @follow.setter
    def follow(self, trc_id):
        libcvht.mandy_set_follow(self._mnd_handle, trc_id)

    @property
    def julia(self):
        return True if libcvht.mandy_get_julia(self._mnd_handle) else False

    @julia.setter
    def julia(self, v):
        libcvht.mandy_set_julia(self._mnd_handle, 1 if v else 0)
