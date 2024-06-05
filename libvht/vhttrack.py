# vhttrack.py - vahatraker (libvht)
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
from libvht.vhtcolumn import VHTColumn
from libvht.vhtctrllist import VHTCtrlList
from libvht.vhtquicklist import VHTQuickList
from libvht.vhtextras import VHTExtras
from libvht.vhtmandy import VHTMandy
from libvht import libcvht


class VHTTrack(Iterable):
    def __init__(self, trk):
        super(VHTTrack, self).__init__()
        self._trk_handle = trk
        self._extras = None

    def __len__(self):
        return libcvht.track_get_ncols(self._trk_handle)

    def __iter__(self):
        for itm in range(self.__len__()):
            yield VHTColumn(self._trk_handle, itm)

    def __int__(self):
        return int(self._trk_handle)

    def clear(self):
        self.ctrl[0].clear()
        for col in self:
            col.clear()

    def __getitem__(self, itm):
        if itm >= self.__len__():
            raise IndexError(itm, "always look on...")

        if itm < 0:
            raise IndexError(itm, "...the bright side of life")

        return VHTColumn(self._trk_handle, itm)

    def __setitem__(self, itm, val):
        pass

    def insert(self, itm, val):
        pass

    def add_column(self):
        libcvht.track_add_col(self._trk_handle)
        return self[self.__len__() - 1]

    def swap_column(self, c1, c2):
        libcvht.track_swap_col(self._trk_handle, c1, c2)

    def del_column(self, c=-1):
        if c == -1:
            libcvht.track_del_col(self._trk_handle, self.__len__() - 1)
        else:
            libcvht.track_del_col(self._trk_handle, c)

    def kill_notes(self):
        libcvht.track_kill_notes(self._trk_handle)

    @property
    def index(self):
        return libcvht.track_get_index(self._trk_handle)

    @property
    def port(self):
        return libcvht.track_get_port(self._trk_handle)

    @port.setter
    def port(self, value):
        self.kill_notes()
        libcvht.track_set_port(self._trk_handle, value)

    @property
    def indicators(self):
        return libcvht.track_get_indicators(self._trk_handle)

    @indicators.setter
    def indicators(self, value):
        libcvht.track_set_indicators(self._trk_handle, value)

    @property
    def dirty(self):
        return libcvht.track_get_dirty(self._trk_handle)

    @dirty.setter
    def dirty(self, value):
        libcvht.track_set_dirty(self._trk_handle, value)

    @property
    def channel(self):
        return libcvht.track_get_channel(self._trk_handle)

    @channel.setter
    def channel(self, value):
        self.kill_notes()
        libcvht.track_set_channel(self._trk_handle, value)

    @property
    def nrows(self):
        return libcvht.track_get_nrows(self._trk_handle)

    @nrows.setter
    def nrows(self, value):
        libcvht.track_set_nrows(self._trk_handle, value)

    @property
    def nsrows(self):
        return libcvht.track_get_nsrows(self._trk_handle)

    @nsrows.setter
    def nsrows(self, value):
        libcvht.track_set_nsrows(self._trk_handle, value)

    @property
    def playing(self):
        return libcvht.track_get_playing(self._trk_handle)

    @playing.setter
    def playing(self, value):
        libcvht.track_set_playing(self._trk_handle, value)

    @property
    def pos(self):
        return libcvht.track_get_pos(self._trk_handle)

    @property
    def ctrl(self):
        return VHTCtrlList(self._trk_handle)

    # number of controllers / envelopes
    @property
    def nctrl(self):
        return libcvht.track_get_nctrl(self._trk_handle)

    # controller rows per row
    @property
    def ctrlpr(self):
        return libcvht.track_get_ctrlpr(self._trk_handle)

    # controller numbers
    @property
    def ctrls(self):
        return eval(libcvht.track_get_ctrl_nums(self._trk_handle))

    @property
    def loop(self):
        return libcvht.track_get_loop(self._trk_handle)

    @loop.setter
    def loop(self, value):
        libcvht.track_set_loop(self._trk_handle, value)

    @property
    def extras(self):
        if not self._extras:
            self._extras = VHTExtras(self._get_extras, self._set_extras)
        return self._extras

    @property
    def mandy(self):
        ret = libcvht.track_get_mandy(self._trk_handle)
        if ret:
            return VHTMandy(ret, self._trk_handle)
        else:
            return None

    def add_mandy(self):
        return VHTMandy(libcvht.track_add_mandy(self._trk_handle), self._trk_handle)

    def del_mandy(self):
        libcvht.track_del_mandy(self._trk_handle)

    def _set_extras(self, value):
        libcvht.track_set_extras(self._trk_handle, value)

    def _get_extras(self):
        return libcvht.track_get_extras(self._trk_handle)

    def send_program_change(self, prog):
        libcvht.track_set_program(self._trk_handle, prog)

    @property
    def prog_send(self):
        return libcvht.track_get_prog_send(self._trk_handle)

    @prog_send.setter
    def prog_send(self, value):
        libcvht.track_set_prog_send(self._trk_handle, 1 if value else 0)

    @property
    def qc1_send(self):
        return libcvht.track_get_qc1_send(self._trk_handle)

    @qc1_send.setter
    def qc1_send(self, value):
        libcvht.track_set_qc1_send(self._trk_handle, 1 if value else 0)

    def set_qc1(self, ctrl, val):
        libcvht.track_set_qc1(self._trk_handle, ctrl, val)

    @property
    def qc2_send(self):
        return libcvht.track_get_qc2_send(self._trk_handle)

    @qc2_send.setter
    def qc2_send(self, value):
        libcvht.track_set_qc2_send(self._trk_handle, 1 if value else 0)

    def set_qc2(self, ctrl, val):
        libcvht.track_set_qc2(self._trk_handle, ctrl, val)

    def set_bank(self, msb, lsb):
        libcvht.track_set_bank(self._trk_handle, msb, lsb)

    def get_program(self):
        return eval(libcvht.track_get_program(self._trk_handle))

    def get_qc(self):
        return eval(libcvht.track_get_qc(self._trk_handle))

    # sets control, r = row * ctrlpr + offset
    def set_ctrl(self, c, r, val):
        return libcvht.track_set_ctrl(self._trk_handle, c, r, val)

    # gets all controls for given row (as they will be played)
    def get_ctrl(self, c, r):
        lpr = self.ctrlpr
        ret_arr = libcvht.int_array(lpr)
        libcvht.track_get_ctrl(self._trk_handle, ret_arr, lpr, c, r)

        return VHTQuickList(ret_arr, lpr)

    # gets all controls for given row (recorded/rendered part/doodles)
    def get_ctrl_rec(self, c, r):
        lpr = self.ctrlpr
        ret_arr = libcvht.int_array(lpr)
        libcvht.track_get_ctrl_rec(self._trk_handle, ret_arr, lpr, c, r)

        return VHTQuickList(ret_arr, lpr)

    # gets all controls for given row (env part)
    def get_ctrl_env(self, c, r):
        lpr = self.ctrlpr
        ret_arr = libcvht.int_array(lpr)
        libcvht.track_get_ctrl_env(self._trk_handle, ret_arr, lpr, c, r)

        return VHTQuickList(ret_arr, lpr)

    # gets last sent controller value
    def get_lctrlval(self, c):
        return libcvht.track_get_lctrlval(self._trk_handle, c)

    # last row played
    def get_last_row_played(self, c):
        return libcvht.track_get_last_row_played(self._trk_handle, c)

    def env_del_node(self, c, n):
        libcvht.track_envelope_del_node(self._trk_handle, c, n)

    def env_add_node(self, c, x, y, z, linked):
        libcvht.track_envelope_add_node(self._trk_handle, c, x, y, z, linked)

    def env_set_node(self, c, n, x, y, z, linked=-1):
        libcvht.track_envelope_set_node(self._trk_handle, c, n, x, y, z, linked)

    def get_envelope(self, c):
        return libcvht.track_get_envelope(self._trk_handle, c)

    def trigger(self):
        libcvht.track_trigger(self._trk_handle)

    def __str__(self):
        ret = ""
        for r in range(self.nrows):
            ret = ret + ("%02d: " % (r))
            for c, rw in enumerate(self):
                rw = self[c][r]
                ret = ret + "| "
                ret = ret + str(rw) + " "

                if rw.type == 1:
                    ret = ret + ("%03d " % (rw.velocity))
                else:
                    ret = ret + "    "

            ret = ret + "|"
            ret = ret + "\n"

        return ret

    def clear_updates(self):
        libcvht.track_clear_updates(self._trk_handle)

    def get_rec_update(self):
        rec = libcvht.track_get_rec_update(self._trk_handle)
        if rec:
            return rec

        return None
