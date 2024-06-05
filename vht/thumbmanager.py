# thumbmanager.py - vahatraker
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

import cairo
import random


class ThumbManager:
    def __init__(self, mod):
        self.mod = mod
        self.thumbs = {}
        self.seqs = {}

    def get(self, seq_id):
        seq = None

        if type(seq_id) is int:
            seq = self.mod[seq_id]
        if type(seq_id) is tuple:
            seq = self.mod.timeline.strips.get_seq(seq_id[1])

        if not seq:
            return None

        if not seq.thumb_dirty:
            if seq_id in self.thumbs:
                return self.thumbs[seq_id]

        td = seq.thumb
        self.thumbs[seq_id] = self.gen(td)
        return self.thumbs[seq_id]

    def gen(self, td):
        h, w = td[0], td[1]

        fmt = cairo.Format.ARGB32
        stride = fmt.stride_for_width(w)

        b = bytearray(stride * h * 4)
        mb = memoryview(b).cast("I")
        for y in range(h):
            for x in range(w):
                addr = (y * stride) + (x * 4)
                addri = addr // 4
                v = td[2 + x + (w * y)]

                if v == 1:
                    mb[addri] = 0x44444444
                elif v == 2:
                    mb[addri] = 0xCCCCCCCC
                elif v == 3:
                    b[addr] = 128
                    b[addr + 1] = random.randint(0, 255)
                    b[addr + 2] = random.randint(0, 255)
                    b[addr + 3] = random.randint(0, 255)
                else:
                    mb[addri] = 0x00000000

        thumb = cairo.SurfacePattern(cairo.ImageSurface.create_for_data(b, fmt, w, h))
        thumb.set_filter(cairo.Filter.NEAREST)
        return thumb

    def clear(self):
        self.thumbs = {}

    def swap(self, s1, s2):
        self.thumbs[s1], self.thumbs[s2] = self.thumbs[s2], self.thumbs[s1]
        nthumbs = {}

        for thid in self.thumbs.keys():
            if type(thid) is tuple:
                if thid[0] == s1:
                    nthumbs[(s2, thid[1])] = self.thumbs[thid]
                if thid[0] == s2:
                    nthumbs[(s1, thid[1])] = self.thumbs[thid]
            else:
                nthumbs[thid] = self.thumbs[thid]

        self.thumbs = nthumbs
