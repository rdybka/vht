# portconfig.py - vahatraker
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


def refresh_connections(mod, cfg):
    if "portconfig" not in mod.extras:
        return

    if mod.render_mode:
        return

    mod.ports.refresh()
    pcfg = mod.extras["portconfig"]

    # inputs
    for inp in pcfg["in"]:
        pfrom = None
        pto = None

        for p in mod.ports:
            if p.name == inp:
                pfrom = p
            if p.mine and p.input:
                pto = p

        if pfrom and pto:
            pfrom.connect(pto)

    need_refr = False
    # outputs
    for p in range(mod.max_ports):
        for prt in pcfg["out"][p]:
            if prt in mod.ports:
                pfrom = None
                pto = None

                if not mod.ports.output_is_open(p):
                    mod.ports.output_open(p)
                    need_refr = True

                pnm = mod.ports.output_get_name(p)

                for pp in mod.ports:
                    if pp.name == pnm:
                        pfrom = pp

                    if pp.name == prt:
                        pto = pp

                if pfrom and pto:
                    pfrom.connect(pto)

    # disable unused outputs
    if need_refr:
        refresh_connections(mod, cfg)
        return

    need_refr = False
    to_close = []
    for p in range(mod.max_ports):
        if mod.ports.output_is_open(p):
            pnm = mod.ports.output_get_name(p)
            prt = mod.ports.get_by_name(pnm)
            if not prt.connections:
                if p > 0:
                    to_close.append(p)
                need_refr = True

    if need_refr:
        for p in to_close:
            mod.ports.output_close(p)

        mod.ports.refresh()

    if "default_out_port" in mod.extras:
        p = mod.extras["default_out_port"]
        mod.default_midi_out_port = p


def close_connections(mod):
    for prt in mod.ports:
        if prt.mine:
            for c in prt.connections:
                prt.disconnect(c)
