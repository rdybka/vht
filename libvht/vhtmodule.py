# vhtmodule.py - vahatraker (libvht)
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
from libvht.vhtsequence import VHTSequence
from libvht.vhttimeline import VHTTimeline
from libvht.vhtports import VHTPorts
import pickle


def pack_seq(seq):
    s = {}
    s["length"] = seq.length
    s["rpb"] = seq.rpb
    s["parent"] = seq.parent
    s["trg_playmode"] = seq.trg_playmode
    s["trg_quantise"] = seq.trg_quantise
    s["trig"] = [
        seq.get_trig(0),
        seq.get_trig(1),
        seq.get_trig(2),
        seq.get_trig(3),
        seq.get_trig(4),
    ]
    s["trig_grp"] = [seq.get_trig_grp(0), seq.get_trig_grp(1)]
    s["playing"] = seq.playing
    s["trk"] = []
    s["extras"] = seq.extras.jsn

    for trk in seq:
        t = {}
        t["port"] = trk.port
        t["channel"] = trk.channel
        t["nrows"] = trk.nrows
        t["nsrows"] = trk.nsrows
        t["playing"] = trk.playing
        t["ctrlpr"] = trk.ctrlpr
        t["program"] = trk.get_program()
        t["qc"] = trk.get_qc()
        t["prog_send"] = trk.prog_send
        t["qc1_send"] = trk.qc1_send
        t["qc2_send"] = trk.qc2_send
        t["loop"] = trk.loop
        t["extras"] = trk.extras.jsn

        t["ctrl"] = []
        for cn, ctrl in enumerate(trk.ctrl):
            c = {}
            c["ctrlnum"] = ctrl.ctrlnum
            c["rows"] = []
            c["doodles"] = []
            rn = 0
            for r in ctrl:
                if r.velocity > -1:
                    rw = {}
                    rw["n"] = rn
                    rw["velocity"] = r.velocity
                    rw["linked"] = r.linked
                    rw["smooth"] = r.smooth
                    rw["anchor"] = r.anchor
                    c["rows"].append(rw)

                rn += 1

            for r in range(trk.nrows):
                dood = trk.get_ctrl_rec(cn, r).as_list()
                empty = True
                for d in dood:
                    if d > -1:
                        empty = False

                if not empty:
                    c["doodles"].append([r, dood])

            t["ctrl"].append(c)

        t["col"] = []
        for col in trk:
            c = []
            rn = 0
            for row in col:
                if row.type > 0:
                    r = {}
                    r["n"] = rn
                    r["type"] = row.type
                    r["note"] = row.note
                    r["velocity"] = row.velocity
                    r["delay"] = row.delay
                    r["prob"] = row.prob
                    r["v_range"] = row.velocity_range
                    r["d_range"] = row.delay_range
                    c.append(r)

                rn += 1
            t["col"].append(c)

        t["mandy"] = trk.mandy.save_state
        s["trk"].append(t)

    return s


class VHTModule(Iterable):
    """
    This is your interface to the VHT magic

    libvht.mod() will return an instance
    """

    def __init__(self):
        super(VHTModule, self).__init__()
        self.active_track = None

        self._mod_handle = libcvht.module_new()
        self._clt_handle = libcvht.module_get_midi_client(self._mod_handle)
        self.extras = {}  # will be saved - used for settings

        self.timeline = VHTTimeline(self)
        self.ports = VHTPorts(self._clt_handle)
        # default values for extras
        self.cb_new_sequence = []  # will be called after new seq with seq_id as param
        self.cb_new_track = []  # will be called after new track with trk_id as param

    def __del__(self):
        libcvht.module_free(self._mod_handle)
        libcvht.midi_stop(self._clt_handle)

    # connect to jack
    def midi_start(self, name=None):
        return libcvht.midi_start(self._clt_handle, name)

    # disconnect from jack
    def midi_stop(self):
        libcvht.midi_stop(self._clt_handle)

    def midi_synch_ports(self):
        libcvht.module_synch_output_ports(self._mod_handle)

    @property
    def ports_changed(self):
        return True if libcvht.midi_port_names_changed(self._clt_handle) else False

    def new(self):
        self.play = 0
        for s in range(len(self)):
            self.del_sequence(0)

        self.extras = {}
        self.reset()

    def __len__(self):
        return libcvht.module_get_nseq(self._mod_handle)

    def __iter__(self):
        for itm in range(self.__len__()):
            yield VHTSequence(
                libcvht.module_get_seq(self._mod_handle, itm), self, self.cb_new_track
            )

    def __getitem__(self, itm):
        if type(itm) is tuple:
            return self.timeline.strips.get_seq(itm[1])
        else:
            if itm >= self.__len__():
                raise IndexError()

            if itm < 0:
                raise IndexError()

            return VHTSequence(
                libcvht.module_get_seq(self._mod_handle, itm), self, self.cb_new_track
            )

    def new_sequence(self, length=-1):
        seq = libcvht.sequence_new(length)
        return VHTSequence(seq, self, self.cb_new_track)

    def add_sequence(self, length=-1):
        seq = libcvht.sequence_new(length)
        libcvht.module_add_sequence(self._mod_handle, seq)
        for cb in self.cb_new_sequence:
            cb(libcvht.sequence_get_index(seq))
        return VHTSequence(seq, self, self.cb_new_track)

    def swap_sequence(self, s1, s2):
        libcvht.module_swap_sequence(self._mod_handle, s1, s2)

    def del_sequence(self, s):
        libcvht.module_del_sequence(self._mod_handle, s)
        libcvht.timeline_update(self.timeline._tl_handle)

    def clone_sequence(self, s):
        seq = None
        if type(s) is int:
            seq = libcvht.sequence_clone(self[s]._seq_handle)
        else:
            seq = libcvht.sequence_clone(
                libcvht.timeline_get_seq(self.timeline._tl_handle, s[1])
            )

            libcvht.sequence_strip_parent(seq)

        libcvht.module_add_sequence(self._mod_handle, seq)
        for cb in self.cb_new_sequence:
            cb(libcvht.sequence_get_index(seq))

        for t in self[len(self) - 1]:
            for cb in self.cb_new_track:
                cb(libcvht.sequence_get_index(seq), t.index)

        return VHTSequence(seq, self, self.cb_new_track)

    def replace_sequence(self, s):  # s: strip_id
        seq = libcvht.sequence_clone(
            libcvht.timeline_get_seq(self.timeline._tl_handle, s)
        )

        libcvht.sequence_strip_parent(seq)

        idx = self.timeline.strips[s].col
        pl = libcvht.sequence_get_playing(libcvht.module_get_seq(self._mod_handle, idx))
        seq = libcvht.module_sequence_replace(self._mod_handle, idx, seq)
        libcvht.sequence_set_playing(seq, pl)

    def __str__(self):
        ret = "seq: %d\n" % self.__len__()
        for itm in self:
            ret = ret + "%d : %d\n" % (len(itm), itm.length)
        return ret

    # sneaky as a dead parrot...
    def sneakily_queue_midi_note_on(self, seq, port, chn, note, velocity):
        libcvht.queue_midi_note_on(self._clt_handle, seq, port, chn, note, velocity)

    def sneakily_queue_midi_note_off(self, seq, port, chn, note):
        libcvht.queue_midi_note_off(self._clt_handle, seq, port, chn, note)

    def sneakily_queue_midi_ctrl(self, seq, trk, value, ctrl):
        libcvht.queue_midi_ctrl(self._clt_handle, seq, trk, value, ctrl)

    def sneakily_queue_midi_in(self, chan, tp, note, vel):
        libcvht.queue_midi_in(self._clt_handle, chan, tp, note, vel)

    def reset(self):
        libcvht.module_reset(self._mod_handle)

    @property
    def jack_error(self):
        return libcvht.module_get_midi_error(self._mod_handle)

    @property
    def play(self):
        return libcvht.module_is_playing(self._mod_handle)

    @property
    def switch_req(self):
        return True if libcvht.module_get_switch_req(self._mod_handle) else False

    @property
    def record(self):
        return libcvht.module_is_recording(self._mod_handle)

    @property
    def jack_pos(self):
        return libcvht.module_get_jack_pos(self._mod_handle)

    @property
    def curr_seq(self):
        cs = libcvht.module_get_curr_seq(self._mod_handle)
        if cs:
            return VHTSequence(cs, self).index
        else:
            return 0

    @curr_seq.setter
    def curr_seq(self, val):
        if type(val) is tuple:
            libcvht.module_set_curr_seq(self._mod_handle, 0, val[1])
        else:
            libcvht.module_set_curr_seq(self._mod_handle, -1, val)

    @property
    def ctrlpr(self):
        return libcvht.module_get_ctrlpr(self._mod_handle)

    @ctrlpr.setter
    def ctrlpr(self, value):
        libcvht.module_set_ctrlpr(self._mod_handle, value)

    @record.setter
    def record(self, value):
        if value:
            libcvht.module_record(self._mod_handle, value)
        else:
            libcvht.module_record(self._mod_handle, 0)

    @play.setter
    def play(self, value):
        if value:
            libcvht.module_play(self._mod_handle, 1)
        else:
            libcvht.module_play(self._mod_handle, 0)
            self.record = 0

    @property
    def render_mode(self):
        return libcvht.module_get_render_mode(self._mod_handle)

    @render_mode.setter
    def render_mode(self, value):
        libcvht.module_set_render_mode(self._mod_handle, int(value))

    def set_lead_out(self, value):
        libcvht.module_set_render_lead_out(self._mod_handle, int(value))

    @property
    def dump_notes(self):
        return 0  # what is this?

    @dump_notes.setter
    def dump_notes(self, n):
        libcvht.module_dump_notes(self._mod_handle, n)

    @property
    def bpm(self):
        return libcvht.module_get_bpm(self._mod_handle)

    @bpm.setter
    def bpm(self, value):
        value = min(max(value, self.min_bpm), self.max_bpm)
        libcvht.module_set_bpm(self._mod_handle, value)
        if len(self.timeline.changes) == 1:
            if self.play_mode == 0:
                self.timeline.changes[0].bpm = value
        # elif mod.play_mode == 0 and len(mod.timeline.changes) == 1:
        # print("here!")

    @property
    def play_mode(self):
        return libcvht.module_get_play_mode(self._mod_handle)

    @play_mode.setter
    def play_mode(self, value):
        v = 1 if value else 0
        libcvht.module_set_play_mode(self._mod_handle, v)

    @property
    def transport(self):
        return True if libcvht.module_get_transport(self._mod_handle) else False

    @transport.setter
    def transport(self, val):
        if val:
            libcvht.module_set_transport(self._mod_handle, 1)
        else:
            libcvht.module_set_transport(self._mod_handle, 0)

    @property
    def time(self):
        return libcvht.module_get_time(self._mod_handle)

    @property
    def max_ports(self):
        return libcvht.module_get_max_ports(self._mod_handle)

    @property
    def min_bpm(self):
        return 1

    @property
    def max_bpm(self):
        return 1023.69  # don't crash the system

    # those two work non-"realtime",
    # ment for gui events
    # actual recording happens in c
    def clear_midi_in(self):
        libcvht.midi_in_clear_events(self._clt_handle)

    def get_midi_in_event(self):
        midin = libcvht.midi_in_get_event(self._clt_handle)
        if midin:
            return eval(midin)
        else:
            return None

    # so we don't record control midi events
    # expects a list of (channel, evt_type, note) tuples
    def set_midi_record_ignore(self, midig):
        libcvht.midi_ignore_buffer_clear(self._clt_handle)
        for ig in midig:
            libcvht.midi_ignore_buffer_add(self._clt_handle, ig[0], ig[1], ig[2])

    @property
    def default_midi_out_port(self):
        return libcvht.get_default_midi_out_port(self._clt_handle)

    @default_midi_out_port.setter
    def default_midi_out_port(self, port):
        libcvht.set_default_midi_out_port(self._clt_handle, port)

    def panic(self, brutal=False):
        libcvht.module_panic(self._mod_handle, 1 if brutal else 0)

    def unpanic(self):
        libcvht.module_unpanic(self._mod_handle)

    @property
    def pnq_hack(self):
        return libcvht.module_get_pnq_hack(self._mod_handle)

    @pnq_hack.setter
    def pnq_hack(self, ph):
        libcvht.module_set_pnq_hack(self._mod_handle, 1 if ph else 0)

    @property
    def inception(self):
        return libcvht.module_get_inception(self._mod_handle)

    @inception.setter
    def inception(self, i):
        libcvht.module_set_inception(self._mod_handle, 1 if i else 0)

    @property
    def is_panicking(self):
        return libcvht.module_is_panicking(self._mod_handle)

    @property
    def should_save(self):
        return True if libcvht.module_get_should_save(self._mod_handle) else False

    @should_save.setter
    def should_save(self, ph):
        libcvht.module_set_should_save(self._mod_handle, 1 if ph else 0)

    @property
    def max_trg_grp(self):
        return libcvht.module_get_max_trg_grp()

    def save(self, filename):
        jm = {}
        jm["bpm"] = self.bpm
        jm["ctrlpr"] = self.ctrlpr
        jm["extras"] = self.extras
        jm["curr_seq"] = self.curr_seq
        jm["play_mode"] = self.play_mode
        jm["playing"] = self.play
        jm["seq"] = []
        for seq in self:
            jm["seq"].append(pack_seq(seq))

        tl = {}
        tl["loop_start"] = self.timeline.loop.start
        tl["loop_end"] = self.timeline.loop.end
        tl["loop_active"] = self.timeline.loop.active

        tl["changes"] = []
        for ch in self.timeline.changes:
            chng = {}
            chng["row"] = ch.row
            chng["bpm"] = ch.bpm
            chng["lnk"] = ch.linked
            tl["changes"].append(chng)
        tl["strips"] = []
        for strip in self.timeline.strips:
            strp = {}
            strp["col"] = strip.col
            strp["start"] = strip.start
            strp["length"] = strip.length
            strp["rpb_start"] = strip.rpb_start
            strp["rpb_end"] = strip.rpb_end
            strp["enabled"] = strip.enabled
            strp["seq"] = pack_seq(strip.seq)
            tl["strips"].append(strp)

        jm["tl"] = tl

        with open(filename, "wb") as f:
            pickle.dump(jm, f)

        self.should_save = False

    def load(self, filename, append=False):
        if not isinstance(filename, str):
            filename = filename.get_path()

        with open(filename, "rb") as f:
            try:
                jm = pickle.load(f)
            except:
                print("Couln't load", filename)
                return False

            self.play = 0

            if not append:
                self.new()
                self.timeline.clear()

                self.bpm = jm["bpm"]
                self.ctrlpr = jm["ctrlpr"]
                self.extras = jm["extras"]
                self.play_mode = jm["play_mode"]

            strp_offset = len(self)

            for seq in jm["seq"]:
                self.unpack_seq(seq, True, append)

            tl = jm["tl"]
            for chng in tl["changes"]:
                if not (append and chng["row"] == 0):
                    if not self.timeline.changes.get_at_qb(chng["row"]):
                        self.timeline.changes.insert(
                            chng["bpm"], chng["row"], chng["lnk"]
                        )

            if not self.timeline.changes.get_at_qb(0):
                self.timeline.changes.insert(self.bpm, 0, 0)

            for strp in tl["strips"]:
                s = self.timeline.strips.insert(
                    strp["col"] + strp_offset,
                    self.unpack_seq(strp["seq"]),
                    strp["start"],
                    strp["length"],
                    strp["rpb_start"],
                    strp["rpb_end"],
                )

                s.enabled = strp["enabled"]

            self.timeline.loop.start = tl["loop_start"]
            self.timeline.loop.end = tl["loop_end"]
            self.timeline.loop.active = tl["loop_active"]

            self.curr_seq = jm["curr_seq"]
            self.midi_synch_ports()

            # fix extras
            for s in self:
                for cb in self.cb_new_sequence:
                    cb(s.index)
                for t in s:
                    for cb in self.cb_new_track:
                        cb(s.index, t.index)

            for s in self.timeline.strips:
                for cb in self.cb_new_sequence:
                    cb(s.seq.index)

                for t in s.seq:
                    for cb in self.cb_new_track:
                        cb(s.seq.index, t.index)

            self.play = jm["playing"]

        self.should_save = False
        return True

    def dump_midi(self, filename, tc=0, ticks=100):
        return libcvht.module_dump_midi(self._mod_handle, filename, tc, ticks)

    def unpack_seq(self, seq, matrix=False, append=False):
        sq = None
        par = -1

        if matrix:
            s = self.add_sequence()
            s.parent = par
        else:
            sq = libcvht.sequence_new(23)
            s = VHTSequence(sq, self)
            par = seq["parent"]

        s.length = seq["length"]
        s.rpb = seq["rpb"]
        s.parent = par
        s.extras.jsn = seq["extras"]

        if "playing" in seq and not append:
            s.playing = seq["playing"]

        if "trg_playmode" in seq:
            s.trg_playmode = seq["trg_playmode"]
            s.trg_quantise = seq["trg_quantise"]

            if "trig_grp" in seq:
                for grp, n in enumerate(seq["trig_grp"]):
                    s.set_trig_grp(grp, n)

            for tr, trig in enumerate(seq["trig"]):
                s.set_trig(tr, *trig)

        for trk in seq["trk"]:
            t = s.add_track(
                trk["port"],
                trk["channel"],
                trk["nrows"],
                trk["nsrows"],
                trk["ctrlpr"],
            )
            t.playing = trk["playing"]
            t.set_bank(trk["program"][0], trk["program"][1])
            t.send_program_change(trk["program"][2])
            t.set_qc1(trk["qc"][0], trk["qc"][1])
            t.set_qc2(trk["qc"][2], trk["qc"][3])

            t.prog_send = True
            t.qc1_send = True
            t.qc2_send = True

            if "prog_send" in trk:
                t.prog_send = trk["prog_send"]

            if "qc1_send" in trk:
                t.qc1_send = trk["qc1_send"]

            if "qc2_send" in trk:
                t.qc2_send = trk["qc2_send"]

            t.loop = trk["loop"]

            t.extras.jsn = trk["extras"]

            nctrl = 0
            for ctrl in trk["ctrl"]:
                if ctrl["ctrlnum"] > -1:
                    t.ctrl.add(ctrl["ctrlnum"])

                for rw in ctrl["rows"]:
                    r = t.ctrl[nctrl][rw["n"]]
                    r.velocity = rw["velocity"]
                    r.linked = rw["linked"]
                    r.smooth = rw["smooth"]
                    r.anchor = rw["anchor"]

                    t.ctrl[nctrl].refresh()

                for dood in ctrl["doodles"]:
                    rn = dood[0] * t.ctrlpr
                    for d in dood[1]:
                        t.set_ctrl(nctrl, rn, d)
                        rn += 1

                nctrl += 1

            for cc, col in enumerate(trk["col"]):
                if cc == 0:
                    c = t[0]
                else:
                    c = t.add_column()

                for row in col:
                    rr = c[row["n"]]
                    rr.type = row["type"]
                    rr.note = row["note"]
                    rr.velocity = row["velocity"]
                    rr.delay = row["delay"]

                    if "prob" in row:
                        rr.prob = row["prob"]

                    if "v_range" in row:
                        rr.velocity_range = row["v_range"]

                    if "d_range" in row:
                        rr.delay_range = row["d_range"]

            if "mandy" in trk:
                t.mandy.init_from(trk["mandy"])

        return sq

    def freewheel_off(self):
        libcvht.module_set_freewheel(self._mod_handle, 0)

    def freewheel_on(self):
        libcvht.module_set_freewheel(self._mod_handle, 1)

    def i2n(self, i):
        return libcvht.i2n(i)
