# filerotator.py - vahatraker
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

from vht import mod, cfg
import os.path


def rotate(fname, n_copies):
    if n_copies == 0:
        return

    basepath, basename = os.path.split(fname)

    for c in range(n_copies, 0, -1):
        fdst = os.path.join(basepath, "~%s.%02d" % (basename, c))
        if c > 1:
            fsrc = os.path.join(basepath, "~%s.%02d" % (basename, c - 1))
        else:
            fsrc = os.path.join(basepath, "%s" % (basename))

        if os.path.isfile(fsrc):
            if os.path.isfile(fdst):
                os.remove(fdst)

            os.rename(fsrc, fdst)
