# vhtmandy.py - Valhalla Tracker (libvht)
#
# Copyright (C) 2020 Remigiusz Dybka - remigiusz.dybka@gmail.com
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

from libvht import libcvht


class VHTMandy:
    def __init__(self, mnd, trk):
        self._trk_handle = trk
        self._mnd_handle = mnd

    def get_pixels(self, w, h, stride):
        return libcvht.mandy_get_pixels(self._mnd_handle, int(w), int(h), stride)

    def set_rgb(self, r, g, b):
        libcvht.mandy_set_rgb(self._mnd_handle, int(r), int(g), int(b))

    def set_xy(self, x, y):
        libcvht.mandy_set_xy(self._mnd_handle, float(x), float(y))

    def render(self, w, h):  # to return pointlist (length)
        return libcvht.mandy_render(self._mnd_handle, int(w), int(h))

    # remove this
    def set_cxy(self, x, y):
        libcvht.mandy_set_cxy(self._mnd_handle, float(x), float(y))

    def screen_translate(self, x, y, w, h):
        libcvht.mandy_translate(
            self._mnd_handle, float(x), float(y), float(w), float(h)
        )

    def screen_rotate(self, x, y, w, h):
        libcvht.mandy_rotate(self._mnd_handle, float(x), float(y), float(w), float(h))

    def screen_zoom(self, x, y, w, h):
        libcvht.mandy_zoom(self._mnd_handle, float(x), float(y), float(w), float(h))

    @property
    def pause(self):
        ret = libcvht.mandy_get_pause(self._mnd_handle)
        return True if ret else False

    @pause.setter
    def pause(self, val):
        libcvht.mandy_set_pause(self._mnd_handle, 1 if val else 0)

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
    def info(self):
        ret = libcvht.mandy_get_info(self._mnd_handle)
        return ret if len(ret) else None
