# This file was automatically generated by SWIG (http://www.swig.org).
# Version 4.0.2
#
# Do not make changes to this file unless you know what you are doing--modify
# the SWIG interface file instead.

from sys import version_info as _swig_python_version_info
if _swig_python_version_info < (2, 7, 0):
    raise RuntimeError("Python 2.7 or later required")

# Import the low-level C/C++ module
if __package__ or "." in __name__:
    from . import _libcvht
else:
    import _libcvht

try:
    import builtins as __builtin__
except ImportError:
    import __builtin__

def _swig_repr(self):
    try:
        strthis = "proxy of " + self.this.__repr__()
    except __builtin__.Exception:
        strthis = ""
    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)


def _swig_setattr_nondynamic_instance_variable(set):
    def set_instance_attr(self, name, value):
        if name == "thisown":
            self.this.own(value)
        elif name == "this":
            set(self, name, value)
        elif hasattr(self, name) and isinstance(getattr(type(self), name), property):
            set(self, name, value)
        else:
            raise AttributeError("You cannot add instance attributes to %s" % self)
    return set_instance_attr


def _swig_setattr_nondynamic_class_variable(set):
    def set_class_attr(cls, name, value):
        if hasattr(cls, name) and not isinstance(getattr(cls, name), property):
            set(cls, name, value)
        else:
            raise AttributeError("You cannot add class attributes to %s" % cls)
    return set_class_attr


def _swig_add_metaclass(metaclass):
    """Class decorator for adding a metaclass to a SWIG wrapped class - a slimmed down version of six.add_metaclass"""
    def wrapper(cls):
        return metaclass(cls.__name__, cls.__bases__, cls.__dict__.copy())
    return wrapper


class _SwigNonDynamicMeta(type):
    """Meta class to enforce nondynamic attributes (no new attributes) for a class"""
    __setattr__ = _swig_setattr_nondynamic_class_variable(type.__setattr__)


class int_array(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr

    def __init__(self, nelements):
        _libcvht.int_array_swiginit(self, _libcvht.new_int_array(nelements))
    __swig_destroy__ = _libcvht.delete_int_array

    def __getitem__(self, index):
        return _libcvht.int_array___getitem__(self, index)

    def __setitem__(self, index, value):
        return _libcvht.int_array___setitem__(self, index, value)

    def cast(self):
        return _libcvht.int_array_cast(self)

    @staticmethod
    def frompointer(t):
        return _libcvht.int_array_frompointer(t)

# Register int_array in _libcvht:
_libcvht.int_array_swigregister(int_array)

def int_array_frompointer(t):
    return _libcvht.int_array_frompointer(t)

class double_array(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr

    def __init__(self, nelements):
        _libcvht.double_array_swiginit(self, _libcvht.new_double_array(nelements))
    __swig_destroy__ = _libcvht.delete_double_array

    def __getitem__(self, index):
        return _libcvht.double_array___getitem__(self, index)

    def __setitem__(self, index, value):
        return _libcvht.double_array___setitem__(self, index, value)

    def cast(self):
        return _libcvht.double_array_cast(self)

    @staticmethod
    def frompointer(t):
        return _libcvht.double_array_frompointer(t)

# Register double_array in _libcvht:
_libcvht.double_array_swigregister(double_array)

def double_array_frompointer(t):
    return _libcvht.double_array_frompointer(t)


def module_new():
    return _libcvht.module_new()

def module_free(mod):
    return _libcvht.module_free(mod)

def module_reset(mod):
    return _libcvht.module_reset(mod)

def module_panic(mod, brutal):
    return _libcvht.module_panic(mod, brutal)

def module_unpanic(mod):
    return _libcvht.module_unpanic(mod)

def module_is_panicking(mod):
    return _libcvht.module_is_panicking(mod)

def module_get_midi_client(mod):
    return _libcvht.module_get_midi_client(mod)

def midi_start(clt, clt_name):
    return _libcvht.midi_start(clt, clt_name)

def midi_stop(clt):
    return _libcvht.midi_stop(clt)

def i2n(i):
    return _libcvht.i2n(i)

def get_midi_error(mod):
    return _libcvht.get_midi_error(mod)

def module_get_time(mod):
    return _libcvht.module_get_time(mod)

def module_get_max_ports(mod):
    return _libcvht.module_get_max_ports(mod)

def module_synch_output_ports(mod):
    return _libcvht.module_synch_output_ports(mod)

def set_default_midi_out_port(clt, port):
    return _libcvht.set_default_midi_out_port(clt, port)

def get_default_midi_out_port(clt):
    return _libcvht.get_default_midi_out_port(clt)

def module_play(mod, arg2):
    return _libcvht.module_play(mod, arg2)

def module_set_render_mode(mod, mode):
    return _libcvht.module_set_render_mode(mod, mode)

def module_get_render_mode(mod):
    return _libcvht.module_get_render_mode(mod)

def module_set_render_lead_out(mod, lead_out):
    return _libcvht.module_set_render_lead_out(mod, lead_out)

def module_set_freewheel(mod, on):
    return _libcvht.module_set_freewheel(mod, on)

def module_is_playing(mod):
    return _libcvht.module_is_playing(mod)

def module_record(mod, arg2):
    return _libcvht.module_record(mod, arg2)

def module_is_recording(mod):
    return _libcvht.module_is_recording(mod)

def module_get_bpm(mod):
    return _libcvht.module_get_bpm(mod)

def module_set_bpm(mod, arg2):
    return _libcvht.module_set_bpm(mod, arg2)

def module_set_transport(mod, t):
    return _libcvht.module_set_transport(mod, t)

def module_get_transport(mod):
    return _libcvht.module_get_transport(mod)

def module_set_pnq_hack(mod, ph):
    return _libcvht.module_set_pnq_hack(mod, ph)

def module_get_pnq_hack(mod):
    return _libcvht.module_get_pnq_hack(mod)

def module_set_inception(mod, i):
    return _libcvht.module_set_inception(mod, i)

def module_get_inception(mod):
    return _libcvht.module_get_inception(mod)

def module_set_should_save(mod, ss):
    return _libcvht.module_set_should_save(mod, ss)

def module_get_should_save(mod):
    return _libcvht.module_get_should_save(mod)

def module_dump_midi(mod, phname, tc, tpf):
    return _libcvht.module_dump_midi(mod, phname, tc, tpf)

def module_get_nseq(mod):
    return _libcvht.module_get_nseq(mod)

def module_get_seq(mod, arg2):
    return _libcvht.module_get_seq(mod, arg2)

def module_add_sequence(mod, seq):
    return _libcvht.module_add_sequence(mod, seq)

def module_del_sequence(mod, s):
    return _libcvht.module_del_sequence(mod, s)

def module_swap_sequence(mod, s1, s2):
    return _libcvht.module_swap_sequence(mod, s1, s2)

def module_sequence_replace(mod, s, seq):
    return _libcvht.module_sequence_replace(mod, s, seq)

def module_get_curr_seq(mod):
    return _libcvht.module_get_curr_seq(mod)

def module_set_curr_seq(mod, t, s):
    return _libcvht.module_set_curr_seq(mod, t, s)

def module_dump_notes(mod, n):
    return _libcvht.module_dump_notes(mod, n)

def module_get_ctrlpr(mod):
    return _libcvht.module_get_ctrlpr(mod)

def module_set_ctrlpr(mod, arg2):
    return _libcvht.module_set_ctrlpr(mod, arg2)

def module_set_play_mode(mod, m):
    return _libcvht.module_set_play_mode(mod, m)

def module_get_play_mode(mod):
    return _libcvht.module_get_play_mode(mod)

def module_get_jack_pos(mod):
    return _libcvht.module_get_jack_pos(mod)

def module_get_switch_req(mod):
    return _libcvht.module_get_switch_req(mod)

def track_get_rec_update(trk):
    return _libcvht.track_get_rec_update(trk)

def track_get_last_row_played(trk, col):
    return _libcvht.track_get_last_row_played(trk, col)

def track_clear_updates(trk):
    return _libcvht.track_clear_updates(trk)

def midi_in_get_event(clt):
    return _libcvht.midi_in_get_event(clt)

def midi_in_clear_events(clt):
    return _libcvht.midi_in_clear_events(clt)

def queue_midi_in(clt, chan, type, note, vel):
    return _libcvht.queue_midi_in(clt, chan, type, note, vel)

def midi_ignore_buffer_clear(clt):
    return _libcvht.midi_ignore_buffer_clear(clt)

def midi_ignore_buffer_add(clt, channel, type, note):
    return _libcvht.midi_ignore_buffer_add(clt, channel, type, note)

def queue_midi_note_on(clt, seq, port, chn, note, velocity):
    return _libcvht.queue_midi_note_on(clt, seq, port, chn, note, velocity)

def queue_midi_note_off(clt, seq, port, chn, note):
    return _libcvht.queue_midi_note_off(clt, seq, port, chn, note)

def queue_midi_ctrl(clt, seq, trk, val, ctrl):
    return _libcvht.queue_midi_ctrl(clt, seq, trk, val, ctrl)

def midi_refresh_port_names(clt):
    return _libcvht.midi_refresh_port_names(clt)

def midi_nport_names(clt):
    return _libcvht.midi_nport_names(clt)

def midi_get_port_name(clt, prt):
    return _libcvht.midi_get_port_name(clt, prt)

def midi_get_port_pname(clt, prtref):
    return _libcvht.midi_get_port_pname(clt, prtref)

def midi_get_port_ref(clt, name):
    return _libcvht.midi_get_port_ref(clt, name)

def midi_get_port_type(prtref):
    return _libcvht.midi_get_port_type(prtref)

def midi_get_port_mine(clt, prtref):
    return _libcvht.midi_get_port_mine(clt, prtref)

def midi_get_port_input(prtref):
    return _libcvht.midi_get_port_input(prtref)

def midi_get_port_output(prtref):
    return _libcvht.midi_get_port_output(prtref)

def midi_get_port_physical(prtref):
    return _libcvht.midi_get_port_physical(prtref)

def midi_get_port_connections(clt, prtref):
    return _libcvht.midi_get_port_connections(clt, prtref)

def midi_get_props(clt):
    return _libcvht.midi_get_props(clt)

def midi_free_charpp(cpp):
    return _libcvht.midi_free_charpp(cpp)

def charpp_nitems(cpp):
    return _libcvht.charpp_nitems(cpp)

def charpp_item(cpp, itm):
    return _libcvht.charpp_item(cpp, itm)

def midi_port_connect(clt, prtref, prtref2):
    return _libcvht.midi_port_connect(clt, prtref, prtref2)

def midi_port_disconnect(clt, prtref, prtref2):
    return _libcvht.midi_port_disconnect(clt, prtref, prtref2)

def midi_port_names_changed(clt):
    return _libcvht.midi_port_names_changed(clt)

def midi_port_is_open(clt, prt):
    return _libcvht.midi_port_is_open(clt, prt)

def midi_close_port(clt, prt):
    return _libcvht.midi_close_port(clt, prt)

def midi_open_port(clt, prt):
    return _libcvht.midi_open_port(clt, prt)

def midi_get_output_port_name(clt, prt):
    return _libcvht.midi_get_output_port_name(clt, prt)

def sequence_new(length):
    return _libcvht.sequence_new(length)

def sequence_get_ntrk(seq):
    return _libcvht.sequence_get_ntrk(seq)

def sequence_get_length(seq):
    return _libcvht.sequence_get_length(seq)

def sequence_get_relative_length(seq):
    return _libcvht.sequence_get_relative_length(seq)

def sequence_get_max_length():
    return _libcvht.sequence_get_max_length()

def sequence_get_index(seq):
    return _libcvht.sequence_get_index(seq)

def sequence_get_parent(seq):
    return _libcvht.sequence_get_parent(seq)

def sequence_set_parent(seq, s):
    return _libcvht.sequence_set_parent(seq, s)

def sequence_set_length(seq, length):
    return _libcvht.sequence_set_length(seq, length)

def sequence_get_trk(seq, n):
    return _libcvht.sequence_get_trk(seq, n)

def sequence_add_track(seq, trk):
    return _libcvht.sequence_add_track(seq, trk)

def sequence_clone_track(seq, trk):
    return _libcvht.sequence_clone_track(seq, trk)

def sequence_del_track(seq, t):
    return _libcvht.sequence_del_track(seq, t)

def sequence_swap_track(seq, t1, t2):
    return _libcvht.sequence_swap_track(seq, t1, t2)

def sequence_get_pos(seq):
    return _libcvht.sequence_get_pos(seq)

def sequence_set_pos(seq, pos):
    return _libcvht.sequence_set_pos(seq, pos)

def sequence_set_midi_focus(seq, foc):
    return _libcvht.sequence_set_midi_focus(seq, foc)

def sequence_double(seq):
    return _libcvht.sequence_double(seq)

def sequence_halve(seq):
    return _libcvht.sequence_halve(seq)

def sequence_set_trg_playmode(seq, v):
    return _libcvht.sequence_set_trg_playmode(seq, v)

def sequence_set_trg_quantise(seq, v):
    return _libcvht.sequence_set_trg_quantise(seq, v)

def sequence_get_trg_playmode(seq):
    return _libcvht.sequence_get_trg_playmode(seq)

def sequence_get_trg_quantise(seq):
    return _libcvht.sequence_get_trg_quantise(seq)

def module_get_max_trg_grp():
    return _libcvht.module_get_max_trg_grp()

def sequence_get_trg_grp(seq, g):
    return _libcvht.sequence_get_trg_grp(seq, g)

def sequence_set_trg_grp(seq, g, grp):
    return _libcvht.sequence_set_trg_grp(seq, g, grp)

def sequence_set_trig(seq, t, tp, ch, nt):
    return _libcvht.sequence_set_trig(seq, t, tp, ch, nt)

def sequence_get_trig(seq, t):
    return _libcvht.sequence_get_trig(seq, t)

def sequence_trigger_mute(seq, nframes):
    return _libcvht.sequence_trigger_mute(seq, nframes)

def sequence_trigger_mute_forward(seq, nframes):
    return _libcvht.sequence_trigger_mute_forward(seq, nframes)

def sequence_trigger_mute_back(seq, nframes):
    return _libcvht.sequence_trigger_mute_back(seq, nframes)

def sequence_trigger_cue(seq, nframes):
    return _libcvht.sequence_trigger_cue(seq, nframes)

def sequence_trigger_cue_forward(seq, nframes):
    return _libcvht.sequence_trigger_cue_forward(seq, nframes)

def sequence_trigger_cue_back(seq, nframes):
    return _libcvht.sequence_trigger_cue_back(seq, nframes)

def sequence_trigger_play_on(seq, nframes):
    return _libcvht.sequence_trigger_play_on(seq, nframes)

def sequence_trigger_play_off(seq, nframes):
    return _libcvht.sequence_trigger_play_off(seq, nframes)

def sequence_get_playing(seq):
    return _libcvht.sequence_get_playing(seq)

def sequence_set_playing(seq, p):
    return _libcvht.sequence_set_playing(seq, p)

def sequence_set_lost(seq, p):
    return _libcvht.sequence_set_lost(seq, p)

def sequence_get_rpb(seq):
    return _libcvht.sequence_get_rpb(seq)

def sequence_set_rpb(seq, rpb):
    return _libcvht.sequence_set_rpb(seq, rpb)

def sequence_get_cue(seq):
    return _libcvht.sequence_get_cue(seq)

def sequence_clone(seq):
    return _libcvht.sequence_clone(seq)

def sequence_strip_parent(seq):
    return _libcvht.sequence_strip_parent(seq)

def sequence_get_thumb(seq, ret, l):
    return _libcvht.sequence_get_thumb(seq, ret, l)

def sequence_get_thumb_dirty(seq):
    return _libcvht.sequence_get_thumb_dirty(seq)

def sequence_get_thumb_length(seq):
    return _libcvht.sequence_get_thumb_length(seq)

def sequence_gen_thumb(seq):
    return _libcvht.sequence_gen_thumb(seq)

def sequence_get_extras(seq):
    return _libcvht.sequence_get_extras(seq)

def sequence_set_extras(seq, extr):
    return _libcvht.sequence_set_extras(seq, extr)

def sequence_rotate(seq, n, trknum):
    return _libcvht.sequence_rotate(seq, n, trknum)

def sequence_get_loop_active(seq):
    return _libcvht.sequence_get_loop_active(seq)

def sequence_set_loop_active(seq, v):
    return _libcvht.sequence_set_loop_active(seq, v)

def sequence_get_loop_start(seq):
    return _libcvht.sequence_get_loop_start(seq)

def sequence_set_loop_start(seq, s):
    return _libcvht.sequence_set_loop_start(seq, s)

def sequence_get_loop_end(seq):
    return _libcvht.sequence_get_loop_end(seq)

def sequence_set_loop_end(seq, e):
    return _libcvht.sequence_set_loop_end(seq, e)

def sequence_get_next_row(seq):
    return _libcvht.sequence_get_next_row(seq)

def track_get_row_ptr(arg1, c, r):
    return _libcvht.track_get_row_ptr(arg1, c, r)

def track_get_ctrlrow_ptr(arg1, c, r):
    return _libcvht.track_get_ctrlrow_ptr(arg1, c, r)

def track_get_index(trk):
    return _libcvht.track_get_index(trk)

def track_get_length(trk):
    return _libcvht.track_get_length(trk)

def track_get_ncols(trk):
    return _libcvht.track_get_ncols(trk)

def track_get_port(trk):
    return _libcvht.track_get_port(trk)

def track_get_channel(trk):
    return _libcvht.track_get_channel(trk)

def track_get_nrows(trk):
    return _libcvht.track_get_nrows(trk)

def track_get_nsrows(trk):
    return _libcvht.track_get_nsrows(trk)

def track_get_playing(trk):
    return _libcvht.track_get_playing(trk)

def track_get_pos(trk):
    return _libcvht.track_get_pos(trk)

def track_set_port(trk, n):
    return _libcvht.track_set_port(trk, n)

def track_set_channel(trk, n):
    return _libcvht.track_set_channel(trk, n)

def track_set_nrows(trk, n):
    return _libcvht.track_set_nrows(trk, n)

def track_set_nsrows(trk, n):
    return _libcvht.track_set_nsrows(trk, n)

def track_set_playing(trk, p):
    return _libcvht.track_set_playing(trk, p)

def track_add_ctrl(trk, ctl):
    return _libcvht.track_add_ctrl(trk, ctl)

def track_del_ctrl(trk, c):
    return _libcvht.track_del_ctrl(trk, c)

def track_clear_ctrl(trk, c):
    return _libcvht.track_clear_ctrl(trk, c)

def track_swap_ctrl(trk, c, c2):
    return _libcvht.track_swap_ctrl(trk, c, c2)

def track_set_ctrl(trk, c, n, val):
    return _libcvht.track_set_ctrl(trk, c, n, val)

def track_get_ctrl(tkl, ret, l, c, n):
    return _libcvht.track_get_ctrl(tkl, ret, l, c, n)

def track_get_ctrl_rec(tkl, ret, l, c, n):
    return _libcvht.track_get_ctrl_rec(tkl, ret, l, c, n)

def track_get_ctrl_env(tkl, ret, l, c, n):
    return _libcvht.track_get_ctrl_env(tkl, ret, l, c, n)

def track_get_ctrl_nums(trk):
    return _libcvht.track_get_ctrl_nums(trk)

def track_set_ctrl_num(trk, c, v):
    return _libcvht.track_set_ctrl_num(trk, c, v)

def track_get_lctrlval(trk, c):
    return _libcvht.track_get_lctrlval(trk, c)

def track_ctrl_refresh_envelope(trk, c):
    return _libcvht.track_ctrl_refresh_envelope(trk, c)

def track_get_nctrl(trk):
    return _libcvht.track_get_nctrl(trk)

def track_get_ctrlpr(trk):
    return _libcvht.track_get_ctrlpr(trk)

def track_get_envelope(trk, c):
    return _libcvht.track_get_envelope(trk, c)

def track_add_col(trk):
    return _libcvht.track_add_col(trk)

def track_del_col(trk, c):
    return _libcvht.track_del_col(trk, c)

def track_swap_col(trk, c, c2):
    return _libcvht.track_swap_col(trk, c, c2)

def track_resize(trk, size):
    return _libcvht.track_resize(trk, size)

def track_double(trk):
    return _libcvht.track_double(trk)

def track_halve(trk):
    return _libcvht.track_halve(trk)

def track_trigger(trk):
    return _libcvht.track_trigger(trk)

def track_kill_notes(trk):
    return _libcvht.track_kill_notes(trk)

def track_set_program(trk, p):
    return _libcvht.track_set_program(trk, p)

def track_set_bank(trk, msb, lsb):
    return _libcvht.track_set_bank(trk, msb, lsb)

def track_set_prog_send(trk, s):
    return _libcvht.track_set_prog_send(trk, s)

def track_get_prog_send(trk):
    return _libcvht.track_get_prog_send(trk)

def track_get_program(trk):
    return _libcvht.track_get_program(trk)

def track_set_qc1_send(trk, s):
    return _libcvht.track_set_qc1_send(trk, s)

def track_get_qc1_send(trk):
    return _libcvht.track_get_qc1_send(trk)

def track_set_qc1(trk, ctrl, val):
    return _libcvht.track_set_qc1(trk, ctrl, val)

def track_set_qc2_send(trk, s):
    return _libcvht.track_set_qc2_send(trk, s)

def track_get_qc2_send(trk):
    return _libcvht.track_get_qc2_send(trk)

def track_set_qc2(trk, ctrl, val):
    return _libcvht.track_set_qc2(trk, ctrl, val)

def track_get_qc(trk):
    return _libcvht.track_get_qc(trk)

def track_set_loop(trk, v):
    return _libcvht.track_set_loop(trk, v)

def track_get_loop(trk):
    return _libcvht.track_get_loop(trk)

def track_get_indicators(trk):
    return _libcvht.track_get_indicators(trk)

def track_set_indicators(trk, i):
    return _libcvht.track_set_indicators(trk, i)

def track_set_dirty(trk, d):
    return _libcvht.track_set_dirty(trk, d)

def track_get_dirty(trk):
    return _libcvht.track_get_dirty(trk)

def track_new(port, channel, len, songlen, ctrlpr):
    return _libcvht.track_new(port, channel, len, songlen, ctrlpr)

def track_get_extras(trk):
    return _libcvht.track_get_extras(trk)

def track_set_extras(trk, extr):
    return _libcvht.track_set_extras(trk, extr)

def track_get_mandy(trk):
    return _libcvht.track_get_mandy(trk)

def row_get_type(rw):
    return _libcvht.row_get_type(rw)

def row_get_note(rw):
    return _libcvht.row_get_note(rw)

def row_get_velocity(rw):
    return _libcvht.row_get_velocity(rw)

def row_get_delay(rw):
    return _libcvht.row_get_delay(rw)

def row_set_type(rw, type):
    return _libcvht.row_set_type(rw, type)

def row_set_note(rw, note):
    return _libcvht.row_set_note(rw, note)

def row_set_velocity(rw, velocity):
    return _libcvht.row_set_velocity(rw, velocity)

def row_set_delay(rw, delay):
    return _libcvht.row_set_delay(rw, delay)

def row_get_prob(rw):
    return _libcvht.row_get_prob(rw)

def row_set_prob(rw, prob):
    return _libcvht.row_set_prob(rw, prob)

def row_get_velocity_range(rw):
    return _libcvht.row_get_velocity_range(rw)

def row_get_delay_range(rw):
    return _libcvht.row_get_delay_range(rw)

def row_set_velocity_range(rw, range):
    return _libcvht.row_set_velocity_range(rw, range)

def row_set_delay_range(rw, range):
    return _libcvht.row_set_delay_range(rw, range)

def row_set(rw, type, note, velocity, delay, prob, v_r, d_r):
    return _libcvht.row_set(rw, type, note, velocity, delay, prob, v_r, d_r)

def ctrlrow_get_velocity(crw):
    return _libcvht.ctrlrow_get_velocity(crw)

def ctrlrow_get_linked(crw):
    return _libcvht.ctrlrow_get_linked(crw)

def ctrlrow_get_smooth(crw):
    return _libcvht.ctrlrow_get_smooth(crw)

def ctrlrow_get_anchor(crw):
    return _libcvht.ctrlrow_get_anchor(crw)

def ctrlrow_set_velocity(crw, v):
    return _libcvht.ctrlrow_set_velocity(crw, v)

def ctrlrow_set_linked(crw, l):
    return _libcvht.ctrlrow_set_linked(crw, l)

def ctrlrow_set_smooth(crw, s):
    return _libcvht.ctrlrow_set_smooth(crw, s)

def ctrlrow_set_anchor(crw, a):
    return _libcvht.ctrlrow_set_anchor(crw, a)

def ctrlrow_set(crw, v, l, s, a):
    return _libcvht.ctrlrow_set(crw, v, l, s, a)

def module_get_timeline(mod):
    return _libcvht.module_get_timeline(mod)

def timeline_set_pos(tl, npos, let_ring):
    return _libcvht.timeline_set_pos(tl, npos, let_ring)

def timeline_get_pos(tl):
    return _libcvht.timeline_get_pos(tl)

def timechange_set_bpm(tl, tc, bpm):
    return _libcvht.timechange_set_bpm(tl, tc, bpm)

def timechange_set_row(tl, tc, row):
    return _libcvht.timechange_set_row(tl, tc, row)

def timechange_set_linked(tl, tc, linked):
    return _libcvht.timechange_set_linked(tl, tc, linked)

def timechange_get_bpm(tc):
    return _libcvht.timechange_get_bpm(tc)

def timechange_get_row(tc):
    return _libcvht.timechange_get_row(tc)

def timechange_get_linked(tc):
    return _libcvht.timechange_get_linked(tc)

def timechange_del(tl, id):
    return _libcvht.timechange_del(tl, id)

def timeline_get_change(tl, id):
    return _libcvht.timeline_get_change(tl, id)

def timeline_change_get_at(tl, row, tol):
    return _libcvht.timeline_change_get_at(tl, row, tol)

def timeline_add_change(tl, bpm, row, linked):
    return _libcvht.timeline_add_change(tl, bpm, row, linked)

def timeline_get_nchanges(tl):
    return _libcvht.timeline_get_nchanges(tl)

def timeline_get_bpm_at_qb(tl, row):
    return _libcvht.timeline_get_bpm_at_qb(tl, row)

def timeline_get_interpol_at_qb(tl, row):
    return _libcvht.timeline_get_interpol_at_qb(tl, row)

def timeline_get_qb(tl, t):
    return _libcvht.timeline_get_qb(tl, t)

def timeline_get_qb_time(tl, row):
    return _libcvht.timeline_get_qb_time(tl, row)

def timeline_get_nticks(tl):
    return _libcvht.timeline_get_nticks(tl)

def timeline_get_tick(tl, n):
    return _libcvht.timeline_get_tick(tl, n)

def timeline_get_length(tl):
    return _libcvht.timeline_get_length(tl)

def timeline_clear(tl):
    return _libcvht.timeline_clear(tl)

def timeline_get_strip(tl, n):
    return _libcvht.timeline_get_strip(tl, n)

def timeline_get_nstrips(tl):
    return _libcvht.timeline_get_nstrips(tl)

def timeline_add_strip(tl, col, seq, start, length, rpb_start, rpb_end):
    return _libcvht.timeline_add_strip(tl, col, seq, start, length, rpb_start, rpb_end)

def timeline_get_strip_for_qb(tl, col, qb):
    return _libcvht.timeline_get_strip_for_qb(tl, col, qb)

def timeline_get_last_strip(tl, col, qb):
    return _libcvht.timeline_get_last_strip(tl, col, qb)

def timeline_expand_start(tl, qb_start):
    return _libcvht.timeline_expand_start(tl, qb_start)

def timeline_expand(tl, qb_start, qb_n):
    return _libcvht.timeline_expand(tl, qb_start, qb_n)

def timeline_del_strip(tl, id):
    return _libcvht.timeline_del_strip(tl, id)

def timeline_get_seq(tl, n):
    return _libcvht.timeline_get_seq(tl, n)

def timeline_get_room(tl, col, qb, ig):
    return _libcvht.timeline_get_room(tl, col, qb, ig)

def timeline_get_snap(tl, tstr_id, qb_delta):
    return _libcvht.timeline_get_snap(tl, tstr_id, qb_delta)

def timeline_place_clone(tl, tstr_id):
    return _libcvht.timeline_place_clone(tl, tstr_id)

def timeline_update(tl):
    return _libcvht.timeline_update(tl)

def timestrip_get_seq(tstr):
    return _libcvht.timestrip_get_seq(tstr)

def timestrip_get_col(tstr):
    return _libcvht.timestrip_get_col(tstr)

def timestrip_get_start(tstr):
    return _libcvht.timestrip_get_start(tstr)

def timestrip_get_length(tstr):
    return _libcvht.timestrip_get_length(tstr)

def timestrip_get_rpb_start(tstr):
    return _libcvht.timestrip_get_rpb_start(tstr)

def timestrip_get_rpb_end(tstr):
    return _libcvht.timestrip_get_rpb_end(tstr)

def timestrip_can_resize_seq(tl, tstr, len):
    return _libcvht.timestrip_can_resize_seq(tl, tstr, len)

def timestrip_can_rpb_seq(tl, tstr, rpb):
    return _libcvht.timestrip_can_rpb_seq(tl, tstr, rpb)

def timestrip_get_enabled(tstr):
    return _libcvht.timestrip_get_enabled(tstr)

def timestrip_set_enabled(tstr, v):
    return _libcvht.timestrip_set_enabled(tstr, v)

def timestrip_noteoffise(tl, tstr):
    return _libcvht.timestrip_noteoffise(tl, tstr)

def timeline_get_prev_seq(tl, tstr):
    return _libcvht.timeline_get_prev_seq(tl, tstr)

def timeline_get_next_seq(tl, tstr):
    return _libcvht.timeline_get_next_seq(tl, tstr)

def timeline_get_loop_active(tl):
    return _libcvht.timeline_get_loop_active(tl)

def timeline_set_loop_active(tl, val):
    return _libcvht.timeline_set_loop_active(tl, val)

def timeline_get_loop_start(tl):
    return _libcvht.timeline_get_loop_start(tl)

def timeline_get_loop_end(tl):
    return _libcvht.timeline_get_loop_end(tl)

def timeline_set_loop_start(tl, val):
    return _libcvht.timeline_set_loop_start(tl, val)

def timeline_set_loop_end(tl, val):
    return _libcvht.timeline_set_loop_end(tl, val)

def timestrip_set_start(tstr, start):
    return _libcvht.timestrip_set_start(tstr, start)

def timestrip_set_col(tstr, col):
    return _libcvht.timestrip_set_col(tstr, col)

def timestrip_set_length(tstr, length):
    return _libcvht.timestrip_set_length(tstr, length)

def timestrip_set_rpb_start(tstr, rpb_start):
    return _libcvht.timestrip_set_rpb_start(tstr, rpb_start)

def timestrip_set_rpb_end(tstr, rpb_end):
    return _libcvht.timestrip_set_rpb_end(tstr, rpb_end)

def parse_note(arg1):
    return _libcvht.parse_note(arg1)

def mandy_get_pixels(mand, width, height, stride):
    return _libcvht.mandy_get_pixels(mand, width, height, stride)

def mandy_render(mand, width, height):
    return _libcvht.mandy_render(mand, width, height)

def mandy_get_points(mand, ret_arr, l):
    return _libcvht.mandy_get_points(mand, ret_arr, l)

def mandy_set_rgb(mand, r, g, b):
    return _libcvht.mandy_set_rgb(mand, r, g, b)

def mandy_set_xy(mand, x, y):
    return _libcvht.mandy_set_xy(mand, x, y)

def mandy_set_cxy(mand, x, y):
    return _libcvht.mandy_set_cxy(mand, x, y)

def mandy_set_jxy(mand, jx, jy):
    return _libcvht.mandy_set_jxy(mand, jx, jy)

def mandy_set_jsx(mand, jsx):
    return _libcvht.mandy_set_jsx(mand, jsx)

def mandy_set_jsy(mand, jsy):
    return _libcvht.mandy_set_jsy(mand, jsy)

def mandy_set_jvx(mand, jvx):
    return _libcvht.mandy_set_jvx(mand, jvx)

def mandy_set_jvy(mand, jvy):
    return _libcvht.mandy_set_jvy(mand, jvy)

def mandy_get_jsx(mand):
    return _libcvht.mandy_get_jsx(mand)

def mandy_get_jsy(mand):
    return _libcvht.mandy_get_jsy(mand)

def mandy_get_jvx(mand):
    return _libcvht.mandy_get_jvx(mand)

def mandy_get_jvy(mand):
    return _libcvht.mandy_get_jvy(mand)

def mandy_set_pause(mand, p):
    return _libcvht.mandy_set_pause(mand, p)

def mandy_get_pause(mand):
    return _libcvht.mandy_get_pause(mand)

def mandy_step(mand):
    return _libcvht.mandy_step(mand)

def mandy_translate(mand, x, y, w, h):
    return _libcvht.mandy_translate(mand, x, y, w, h)

def mandy_translate_julia(mand, x, y, w, h):
    return _libcvht.mandy_translate_julia(mand, x, y, w, h)

def mandy_rotate(mand, x, y, w, h):
    return _libcvht.mandy_rotate(mand, x, y, w, h)

def mandy_zoom(mand, x, y, w, h):
    return _libcvht.mandy_zoom(mand, x, y, w, h)

def mandy_set_active(mand, active):
    return _libcvht.mandy_set_active(mand, active)

def mandy_get_active(mand):
    return _libcvht.mandy_get_active(mand)

def mandy_get_info(mand):
    return _libcvht.mandy_get_info(mand)

def mandy_set_info(mand, info):
    return _libcvht.mandy_set_info(mand, info)

def mandy_get_zoom(mand):
    return _libcvht.mandy_get_zoom(mand)

def mandy_set_zoom(mand, zoom):
    return _libcvht.mandy_set_zoom(mand, zoom)

def mandy_get_rot(mand):
    return _libcvht.mandy_get_rot(mand)

def mandy_set_rot(mand, rot):
    return _libcvht.mandy_set_rot(mand, rot)

def mandy_get_bail(mand):
    return _libcvht.mandy_get_bail(mand)

def mandy_set_bail(mand, bail):
    return _libcvht.mandy_set_bail(mand, bail)

def mandy_get_miter(mand):
    return _libcvht.mandy_get_miter(mand)

def mandy_set_miter(mand, miter):
    return _libcvht.mandy_set_miter(mand, miter)

def mandy_get_max_iter(mand):
    return _libcvht.mandy_get_max_iter(mand)

def mandy_set_julia(mand, v):
    return _libcvht.mandy_set_julia(mand, v)

def mandy_get_julia(mand):
    return _libcvht.mandy_get_julia(mand)

def mandy_get_max_speed():
    return _libcvht.mandy_get_max_speed()

def mandy_reinit_from_scan(mand):
    return _libcvht.mandy_reinit_from_scan(mand)

def mandy_reset(mand):
    return _libcvht.mandy_reset(mand)

def mandy_reset_anim(mand):
    return _libcvht.mandy_reset_anim(mand)

def mandy_save(mand):
    return _libcvht.mandy_save(mand)

def mandy_restore(mand, o):
    return _libcvht.mandy_restore(mand, o)

def mandy_get_ntracies(mand):
    return _libcvht.mandy_get_ntracies(mand)

def mandy_get_tracy(mand, trc_id):
    return _libcvht.mandy_get_tracy(mand, trc_id)

def mandy_get_scan_tracy(mand):
    return _libcvht.mandy_get_scan_tracy(mand)

def mandy_get_init_tracy(mand):
    return _libcvht.mandy_get_init_tracy(mand)

def mandy_set_follow(mand, trc_id):
    return _libcvht.mandy_set_follow(mand, trc_id)

def mandy_get_follow(mand):
    return _libcvht.mandy_get_follow(mand)

def tracy_get_pos(trc):
    return _libcvht.tracy_get_pos(trc)

def tracy_get_disp(trc):
    return _libcvht.tracy_get_disp(trc)

def tracy_get_tail(trc):
    return _libcvht.tracy_get_tail(trc)

def tracy_get_speed(trc):
    return _libcvht.tracy_get_speed(trc)

def tracy_set_speed(trc, s):
    return _libcvht.tracy_set_speed(trc, s)

def tracy_get_scale(trc):
    return _libcvht.tracy_get_scale(trc)

def tracy_set_scale(trc, s):
    return _libcvht.tracy_set_scale(trc, s)

def tracy_get_phase(trc):
    return _libcvht.tracy_get_phase(trc)

def tracy_set_phase(trc, p):
    return _libcvht.tracy_set_phase(trc, p)

def tracy_get_mult(trc):
    return _libcvht.tracy_get_mult(trc)

def tracy_set_mult(trc, m):
    return _libcvht.tracy_set_mult(trc, m)

def tracy_get_zoom(trc):
    return _libcvht.tracy_get_zoom(trc)

def tracy_set_zoom(trc, z):
    return _libcvht.tracy_set_zoom(trc, z)

def tracy_get_qnt(trc):
    return _libcvht.tracy_get_qnt(trc)

def tracy_set_qnt(trc, q):
    return _libcvht.tracy_set_qnt(trc, q)


