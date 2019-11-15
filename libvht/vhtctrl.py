# vhtctrl.py - Valhalla Tracker (libvht)
#
# Copyright (C) 2019 Remigiusz Dybka - remigiusz.dybka@gmail.com
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
from libvht.vhtctrlrow import VHTCtrlRow


class VHTCtrl(Iterable):
    def __init__(self, vht, trk, ctrl, ctrlnum, on_change=None):
        self._vht_handle = vht
        self._trk_handle = trk
        self._ctrl = ctrl
        self._ctrlnum = ctrlnum
        self.on_change = on_change
        super()

    def __len__(self):
        return self._vht_handle.track_get_length(self._trk_handle)

    def clear(self):
        for r in self:
            r.clear()

    def __iter__(self):
        for i in range(self.__len__()):
            yield VHTCtrlRow(
                self._vht_handle,
                self._vht_handle.track_get_ctrlrow_ptr(self._trk_handle, self._ctrl, i),
            )

    def __setitem__(self, itm, val):
        self[itm].velocity = val[0]
        self[itm].linked = val[1]
        self[itm].smooth = val[2]
        self[itm].anchor = val[3]

    def __getitem__(self, itm):
        if itm >= self.__len__():
            raise IndexError(itm)

        if itm < 0:
            raise IndexError(itm)

        return VHTCtrlRow(
            self._vht_handle,
            self._vht_handle.track_get_ctrlrow_ptr(self._trk_handle, self._ctrl, itm),
        )

    def refresh(self):
        self._vht_handle.track_ctrl_refresh_envelope(self._trk_handle, self._ctrl)

    @property
    def ctrlnum(self):
        return self._ctrlnum

    @ctrlnum.setter
    def ctrlnum(self, value):
        if self._ctrlnum == -1:
            return

        self._ctrlnum = int(value)
        self._vht_handle.track_set_ctrl_num(self._trk_handle, self._ctrl, self._ctrlnum)
        if self.on_change:
            self.on_change()

    def __str__(self):
        ret = "ctrl %d:\n" % self._ctrlnum
        for r in range(self.__len__()):
            ret = ret + str(self[r])
            ret = ret + "\n"

        return ret

    def swap(self, c1, c2):
        self._vht_handle.track_swap_ctrl(self._trk_handle, c1, c2)
