# console.py - vahatraker
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
from code import InteractiveConsole, InteractiveInterpreter
from queue import Queue
import sys
import threading
import cairo

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Vte", "2.91")

from gi.repository import Gdk, Gtk, Gio, Vte, Pango


class VHTCons(InteractiveConsole):
    def __init__(self, loc, trm):
        super(VHTCons, self).__init__(loc)
        self.trm = trm
        self.d = True

        self.q = Queue()

        self.autoexec = """
import sys
from vht import mod, cfg
tl = mod.timeline
"""

        for line in self.autoexec.split("\n"):
            self.runsource(line)

        self.runsource("sys.stdout = mod.termfile")
        self.runsource("sys.stdin = mod.termfile")
        if cfg.console_steal_stderr:
            self.runsource("sys.stderr = mod.termfile")


class HackerIO(object):
    def __init__(self, trm):
        self._trm = trm
        self.q = None
        self.stdout = sys.stdout

    def write(self, data):
        self._trm.feed(data.replace("\n", "\r\n").encode())
        if mod.mainwin.get_realized():
            mod.mainwin.show_console()
        # self.stdout.write(data)

    def readline(self):
        return self.q.get()

    def flush(self):
        self.stdout.flush()


class Console(Vte.Terminal):
    def __init__(self):
        super(Console, self).__init__()
        self.buff = ""
        self.history = []
        self.browsing = False
        self.hist_ptr = 0

        self.refresh()

        self.set_font_scale(cfg.console_scale)
        self.set_rewrap_on_resize(True)
        self.set_scroll_on_output(True)
        self.set_scroll_on_keystroke(True)

        self.fs = int(cfg.console_scale * 50)
        self.set_input_enabled(True)
        mod.termfile = HackerIO(self)

        self.connect("key-press-event", self.on_key_press)
        self.connect("scroll-event", self.on_scroll)

        self.cons = VHTCons(locals(), self)
        mod.termfile.q = self.cons.q
        t = threading.Thread(target=self.cons.interact)
        t.daemon = True

        t.start()

    def refresh(self):
        self.set_color_background(
            Gdk.RGBA(*(col * cfg.intensity_background for col in cfg.console_colour), 1)
        )
        self.set_color_foreground(
            Gdk.RGBA(*(col * cfg.intensity_txt for col in cfg.console_colour), 1)
        )

        self.set_font(Pango.FontDescription.from_string(cfg.console_font))

    def on_scroll(self, widget, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK:  # we're zooming!
            if event.delta_y < 0:
                self.fs += 2
                self.fs = min(100, self.fs)

            if event.delta_y > 0:
                self.fs -= 2
                self.fs = max(15, self.fs)

            scale = self.fs / 50.0
            cfg.console_scale = scale
            self.set_font_scale(scale)
            return True

        return False

    def on_key_press(self, widget, event):
        shift = False
        ctrl = False
        alt = False

        if event.state:
            if event.state & Gdk.ModifierType.SHIFT_MASK:
                shift = True

            if event.state & Gdk.ModifierType.CONTROL_MASK:
                ctrl = True

            if event.state & Gdk.ModifierType.MOD1_MASK:
                alt = True

        key = Gdk.keyval_to_unicode(event.keyval)
        key_name = Gdk.keyval_name(event.keyval)

        # print(key, key_name)

        if (key >= 32 and key < 127) or key == 9 or key == 27:
            t = "%c" % key
            self.buff += t
            self.feed(t.encode())

        if key == 13 or key_name == "KP_Enter":
            if not self.buff:
                self.buff = " "
            self.browsing = False
            self.history.append(self.buff)
            self.buff += "\r\n"
            self.cons.q.put(self.buff)
            self.buff = ""
            print()  # :)

        if key == 8:  # backspace
            if self.buff:
                self.buff = self.buff[:-1]
                self.feed("\x1B[1D \x1B[1D".encode())

        if key_name == "Up":
            if not self.browsing:  # first press
                self.browsing = True
                if self.history:
                    self.hist_ptr = len(self.history)

            if self.history:
                for c in self.buff:
                    self.feed("\x1B[1D \x1B[1D".encode())

                self.hist_ptr = max(self.hist_ptr - 1, 0)

                self.buff = self.history[self.hist_ptr]
                self.feed(self.buff.encode())

        if key_name == "Down":
            if not self.browsing:
                return False

            if self.history:
                for c in self.buff:
                    self.feed("\x1B[1D \x1B[1D".encode())

                self.hist_ptr += 1
                if self.hist_ptr >= len(self.history):
                    self.browsing = False

                    self.buff = ""
                else:
                    self.buff = self.history[self.hist_ptr]
                    self.feed(self.buff.encode())

        return True
