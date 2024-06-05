# renderer.py - vahatraker
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

import subprocess
import os
from datetime import datetime


class Renderer:
    def __init__(self, mod, cfg):
        self.mod = mod
        self.cfg = cfg

        self._proc = None

        self._avail = True
        self._pre_delay_start = 0
        self._finished = False
        self._queue = []
        self._seqs = []
        self._orig_pm = None
        self._midi_file = None

        try:
            prc = subprocess.Popen(
                ["jack_capture", "--version"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            outs, errs = prc.communicate()
        except:
            self._avail = False

    @property
    def running(self):
        if self._pre_delay_start:
            t = datetime.now() - self._pre_delay_start
            t = float(t.seconds) + t.microseconds / 1000000

            if t > 0.5:  # or self.mod.render_mode == 3:
                self._pre_delay_start = 0
                self.mod.play = 1

                if self.mod.render_mode == 3:
                    self.mod.freewheel_on()

        if self._pre_delay_start:
            return True

        if self.mod.render_mode == 23 and self.mod.play == 0:
            self.mod.freewheel_off()

            if self.mod.play_mode == 1:
                self.mod.play_mode = self._orig_pm
            if self._proc:
                stdout, stderr = self._proc.communicate(input="\n", timeout=5)
                if self._midi_file:
                    self.mod.dump_midi(
                        self._midi_file, self.cfg.render_timecode, self.cfg.render_ticks
                    )
                self._proc = None
            if self._queue:
                self.start_queue()
            else:
                self._finished = True
                self.mod.mainwin.timeline_view.follow = False
                if self._proc:
                    self._proc.terminate()
                self.mod.render_mode = 0
                if self._seqs:
                    for s in self.mod:
                        s.playing = 0
                    for s in self._seqs:
                        self.mod[s].playing = 1

        if self._finished:
            return False

        if not self._proc:
            return False

        return True

    @property
    def available(self):
        return self._avail

    @property
    def finished(self):
        return self._finished

    def start_live(self, folder, filename, fmt, meter):
        opts = ["jack_capture"]
        opts.append("-f")
        opts.append(fmt)
        opts.append("-fp")
        opts.append(os.path.join(folder, filename + "_"))
        if self.cfg.render_midi:
            self._midi_file = os.path.join(folder, filename + ".mid")
        else:
            self._midi_file = None

        meters = ["none", "vu", "ppm", "dpm", "jf", "sco"]
        if meter > 0:
            opts.append("-mb")
            opts.append("-mt")
            opts.append(meters[meter])

        self._orig_pm = self.mod.play_mode

        self._proc = subprocess.Popen(
            opts,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        self._finished = False

    def start_wudh(self, folder, filename, fmt, meter):
        self._finished = False

        opts = ["jack_capture"]
        opts.append("-jf")
        opts.append("-f")
        opts.append(fmt)
        opts.append("-fp")
        opts.append(os.path.join(folder, filename + "_"))
        if self.cfg.render_midi:
            self._midi_file = os.path.join(folder, filename + ".mid")
        else:
            self._midi_file = None

        self.mod.render_mode = 3
        self._orig_pm = self.mod.play_mode

        self._proc = subprocess.Popen(
            opts,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )

        self._pre_delay_start = datetime.now()

    def start_queue(self):
        seqid = self._queue[0]
        del self._queue[0]

        folder = self._qopts[0]
        filename = self._qopts[1]
        fmt = self._qopts[2]
        lead_out = self._qopts[3]

        opts = ["jack_capture"]
        opts.append("-jf")
        opts.append("-f")
        opts.append(fmt)
        opts.append("-fp")
        opts.append(os.path.join(folder, filename + ("_seq%02d" % seqid) + "_"))
        if self.cfg.render_midi:
            self._midi_file = os.path.join(folder, filename + ("_seq%02d.mid" % seqid))

        self.mod.play = 0
        self.mod.reset()
        self.mod.reset()  # in case some old note-offs hang
        for s in self.mod:
            s.playing = False

        self.mod.render_mode = 1
        self._orig_pm = self.mod.play_mode
        self.mod.play_mode = 0
        self.mod.set_lead_out(lead_out)

        for m in self.mod:
            if m.index == seqid:
                m.playing = 1
            else:
                m.playing = 0

        self._proc = subprocess.Popen(
            opts,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        self._pre_delay_start = datetime.now()

    def start_sequence(self, folder, filename, fmt, lead_out):
        self._finished = False
        self._queue = []
        self._seqs = []
        self._qopts = [folder, filename, fmt, lead_out]
        for s in self.mod:
            if s.playing:
                self._queue.append(s.index)
                self._seqs.append(s.index)

        if self._queue:
            self.start_queue()
        else:
            self._finished = True

    def start_timeline(self, folder, filename, fmt, lead_out):
        self._finished = False

        opts = ["jack_capture"]
        opts.append("-jf")
        opts.append("-f")
        opts.append(fmt)
        opts.append("-fp")
        opts.append(os.path.join(folder, filename + "_"))
        if self.cfg.render_midi:
            self._midi_file = os.path.join(folder, filename + ".mid")
        else:
            self._midi_file = None

        self.mod.play = 0
        self.mod.reset()
        self._seqs = []
        for s in self.mod:
            if s.playing:
                self._seqs.append(s.index)
            s.playing = False

        self._orig_pm = self.mod.play_mode

        self.mod.play_mode = 1
        self.mod.render_mode = 2
        self.mod.set_lead_out(lead_out)
        if self.mod.timeline.loop.active:
            self.mod.timeline.pos = self.mod.timeline.loop.start

        self._proc = subprocess.Popen(
            opts,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )

        self._pre_delay_start = datetime.now()

    def stop(self):
        if self.mod.render_mode == 3:
            self.mod.freewheel_off()

        self.mod.mainwin.timeline_view.follow = False

        if self._proc:
            stdout, stderr = self._proc.communicate(input="\n", timeout=5)
            self._proc = None
            self._queue = []
            self._finished = True
            if self._midi_file:
                self.mod.dump_midi(
                    self._midi_file, self.cfg.render_timecode, self.cfg.render_ticks
                )
            self.mod.render_mode = 0
