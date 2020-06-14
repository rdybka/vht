# This file was automatically generated by SWIG (http://www.swig.org).
# Version 3.0.12
#
# Do not make changes to this file unless you know what you are doing--modify
# the SWIG interface file instead.

from sys import version_info as _swig_python_version_info
if _swig_python_version_info >= (2, 7, 0):
    def swig_import_helper():
        import importlib
        pkg = __name__.rpartition('.')[0]
        mname = '.'.join((pkg, '_libcvht')).lstrip('.')
        try:
            return importlib.import_module(mname)
        except ImportError:
            return importlib.import_module('_libcvht')
    _libcvht = swig_import_helper()
    del swig_import_helper
elif _swig_python_version_info >= (2, 6, 0):
    def swig_import_helper():
        from os.path import dirname
        import imp
        fp = None
        try:
            fp, pathname, description = imp.find_module('_libcvht', [dirname(__file__)])
        except ImportError:
            import _libcvht
            return _libcvht
        try:
            _mod = imp.load_module('_libcvht', fp, pathname, description)
        finally:
            if fp is not None:
                fp.close()
        return _mod
    _libcvht = swig_import_helper()
    del swig_import_helper
else:
    import _libcvht
del _swig_python_version_info

try:
    _swig_property = property
except NameError:
    pass  # Python < 2.2 doesn't have 'property'.

try:
    import builtins as __builtin__
except ImportError:
    import __builtin__

def _swig_setattr_nondynamic(self, class_type, name, value, static=1):
    if (name == "thisown"):
        return self.this.own(value)
    if (name == "this"):
        if type(value).__name__ == 'SwigPyObject':
            self.__dict__[name] = value
            return
    method = class_type.__swig_setmethods__.get(name, None)
    if method:
        return method(self, value)
    if (not static):
        if _newclass:
            object.__setattr__(self, name, value)
        else:
            self.__dict__[name] = value
    else:
        raise AttributeError("You cannot add attributes to %s" % self)


def _swig_setattr(self, class_type, name, value):
    return _swig_setattr_nondynamic(self, class_type, name, value, 0)


def _swig_getattr(self, class_type, name):
    if (name == "thisown"):
        return self.this.own()
    method = class_type.__swig_getmethods__.get(name, None)
    if method:
        return method(self)
    raise AttributeError("'%s' object has no attribute '%s'" % (class_type.__name__, name))


def _swig_repr(self):
    try:
        strthis = "proxy of " + self.this.__repr__()
    except __builtin__.Exception:
        strthis = ""
    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)

try:
    _object = object
    _newclass = 1
except __builtin__.Exception:
    class _object:
        pass
    _newclass = 0

class int_array(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, int_array, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, int_array, name)
    __repr__ = _swig_repr

    def __init__(self, nelements):
        this = _libcvht.new_int_array(nelements)
        try:
            self.this.append(this)
        except __builtin__.Exception:
            self.this = this
    __swig_destroy__ = _libcvht.delete_int_array
    __del__ = lambda self: None

    def __getitem__(self, index):
        return _libcvht.int_array___getitem__(self, index)

    def __setitem__(self, index, value):
        return _libcvht.int_array___setitem__(self, index, value)

    def cast(self):
        return _libcvht.int_array_cast(self)
    if _newclass:
        frompointer = staticmethod(_libcvht.int_array_frompointer)
    else:
        frompointer = _libcvht.int_array_frompointer
int_array_swigregister = _libcvht.int_array_swigregister
int_array_swigregister(int_array)

def int_array_frompointer(t):
    return _libcvht.int_array_frompointer(t)
int_array_frompointer = _libcvht.int_array_frompointer


def module_new():
    return _libcvht.module_new()
module_new = _libcvht.module_new

def module_free(mod):
    return _libcvht.module_free(mod)
module_free = _libcvht.module_free

def module_reset(mod):
    return _libcvht.module_reset(mod)
module_reset = _libcvht.module_reset

def module_panic(mod):
    return _libcvht.module_panic(mod)
module_panic = _libcvht.module_panic

def module_get_midi_client(mod):
    return _libcvht.module_get_midi_client(mod)
module_get_midi_client = _libcvht.module_get_midi_client

def midi_start(clt, clt_name):
    return _libcvht.midi_start(clt, clt_name)
midi_start = _libcvht.midi_start

def midi_stop(clt):
    return _libcvht.midi_stop(clt)
midi_stop = _libcvht.midi_stop

def get_midi_error(mod):
    return _libcvht.get_midi_error(mod)
get_midi_error = _libcvht.get_midi_error

def module_get_time(mod):
    return _libcvht.module_get_time(mod)
module_get_time = _libcvht.module_get_time

def module_get_max_ports(mod):
    return _libcvht.module_get_max_ports(mod)
module_get_max_ports = _libcvht.module_get_max_ports

def module_synch_output_ports(mod):
    return _libcvht.module_synch_output_ports(mod)
module_synch_output_ports = _libcvht.module_synch_output_ports

def module_play(mod, arg2):
    return _libcvht.module_play(mod, arg2)
module_play = _libcvht.module_play

def module_is_playing(mod):
    return _libcvht.module_is_playing(mod)
module_is_playing = _libcvht.module_is_playing

def module_record(mod, arg2):
    return _libcvht.module_record(mod, arg2)
module_record = _libcvht.module_record

def module_is_recording(mod):
    return _libcvht.module_is_recording(mod)
module_is_recording = _libcvht.module_is_recording

def module_get_bpm(mod):
    return _libcvht.module_get_bpm(mod)
module_get_bpm = _libcvht.module_get_bpm

def module_set_bpm(mod, arg2):
    return _libcvht.module_set_bpm(mod, arg2)
module_set_bpm = _libcvht.module_set_bpm

def module_get_nseq(mod):
    return _libcvht.module_get_nseq(mod)
module_get_nseq = _libcvht.module_get_nseq

def module_get_seq(mod, arg2):
    return _libcvht.module_get_seq(mod, arg2)
module_get_seq = _libcvht.module_get_seq

def module_add_sequence(mod, seq):
    return _libcvht.module_add_sequence(mod, seq)
module_add_sequence = _libcvht.module_add_sequence

def module_del_sequence(mod, s):
    return _libcvht.module_del_sequence(mod, s)
module_del_sequence = _libcvht.module_del_sequence

def module_swap_sequence(mod, s1, s2):
    return _libcvht.module_swap_sequence(mod, s1, s2)
module_swap_sequence = _libcvht.module_swap_sequence

def module_get_curr_seq(mod):
    return _libcvht.module_get_curr_seq(mod)
module_get_curr_seq = _libcvht.module_get_curr_seq

def module_set_curr_seq(mod, s):
    return _libcvht.module_set_curr_seq(mod, s)
module_set_curr_seq = _libcvht.module_set_curr_seq

def module_dump_notes(mod, n):
    return _libcvht.module_dump_notes(mod, n)
module_dump_notes = _libcvht.module_dump_notes

def module_get_ctrlpr(mod):
    return _libcvht.module_get_ctrlpr(mod)
module_get_ctrlpr = _libcvht.module_get_ctrlpr

def module_set_ctrlpr(mod, arg2):
    return _libcvht.module_set_ctrlpr(mod, arg2)
module_set_ctrlpr = _libcvht.module_set_ctrlpr

def module_set_play_mode(mod, m):
    return _libcvht.module_set_play_mode(mod, m)
module_set_play_mode = _libcvht.module_set_play_mode

def module_get_play_mode(mod):
    return _libcvht.module_get_play_mode(mod)
module_get_play_mode = _libcvht.module_get_play_mode

def module_get_jack_pos(mod):
    return _libcvht.module_get_jack_pos(mod)
module_get_jack_pos = _libcvht.module_get_jack_pos

def track_get_rec_update(trk):
    return _libcvht.track_get_rec_update(trk)
track_get_rec_update = _libcvht.track_get_rec_update

def track_clear_updates(trk):
    return _libcvht.track_clear_updates(trk)
track_clear_updates = _libcvht.track_clear_updates

def midi_in_get_event(clt):
    return _libcvht.midi_in_get_event(clt)
midi_in_get_event = _libcvht.midi_in_get_event

def midi_in_clear_events(clt):
    return _libcvht.midi_in_clear_events(clt)
midi_in_clear_events = _libcvht.midi_in_clear_events

def midi_ignore_buffer_clear(clt):
    return _libcvht.midi_ignore_buffer_clear(clt)
midi_ignore_buffer_clear = _libcvht.midi_ignore_buffer_clear

def midi_ignore_buffer_add(clt, channel, type, note):
    return _libcvht.midi_ignore_buffer_add(clt, channel, type, note)
midi_ignore_buffer_add = _libcvht.midi_ignore_buffer_add

def queue_midi_note_on(clt, seq, port, chn, note, velocity):
    return _libcvht.queue_midi_note_on(clt, seq, port, chn, note, velocity)
queue_midi_note_on = _libcvht.queue_midi_note_on

def queue_midi_note_off(clt, seq, port, chn, note):
    return _libcvht.queue_midi_note_off(clt, seq, port, chn, note)
queue_midi_note_off = _libcvht.queue_midi_note_off

def queue_midi_ctrl(clt, seq, trk, val, ctrl):
    return _libcvht.queue_midi_ctrl(clt, seq, trk, val, ctrl)
queue_midi_ctrl = _libcvht.queue_midi_ctrl

def set_default_midi_port(mod, port):
    return _libcvht.set_default_midi_port(mod, port)
set_default_midi_port = _libcvht.set_default_midi_port

def module_get_timeline(mod):
    return _libcvht.module_get_timeline(mod)
module_get_timeline = _libcvht.module_get_timeline

def sequence_new(length):
    return _libcvht.sequence_new(length)
sequence_new = _libcvht.sequence_new

def sequence_get_ntrk(seq):
    return _libcvht.sequence_get_ntrk(seq)
sequence_get_ntrk = _libcvht.sequence_get_ntrk

def sequence_get_length(seq):
    return _libcvht.sequence_get_length(seq)
sequence_get_length = _libcvht.sequence_get_length

def sequence_get_max_length():
    return _libcvht.sequence_get_max_length()
sequence_get_max_length = _libcvht.sequence_get_max_length

def sequence_get_index(seq):
    return _libcvht.sequence_get_index(seq)
sequence_get_index = _libcvht.sequence_get_index

def sequence_set_length(seq, length):
    return _libcvht.sequence_set_length(seq, length)
sequence_set_length = _libcvht.sequence_set_length

def sequence_get_trk(seq, n):
    return _libcvht.sequence_get_trk(seq, n)
sequence_get_trk = _libcvht.sequence_get_trk

def sequence_add_track(seq, trk):
    return _libcvht.sequence_add_track(seq, trk)
sequence_add_track = _libcvht.sequence_add_track

def sequence_clone_track(seq, trk):
    return _libcvht.sequence_clone_track(seq, trk)
sequence_clone_track = _libcvht.sequence_clone_track

def sequence_del_track(seq, t):
    return _libcvht.sequence_del_track(seq, t)
sequence_del_track = _libcvht.sequence_del_track

def sequence_swap_track(seq, t1, t2):
    return _libcvht.sequence_swap_track(seq, t1, t2)
sequence_swap_track = _libcvht.sequence_swap_track

def sequence_get_pos(seq):
    return _libcvht.sequence_get_pos(seq)
sequence_get_pos = _libcvht.sequence_get_pos

def sequence_set_midi_focus(seq, foc):
    return _libcvht.sequence_set_midi_focus(seq, foc)
sequence_set_midi_focus = _libcvht.sequence_set_midi_focus

def sequence_double(seq):
    return _libcvht.sequence_double(seq)
sequence_double = _libcvht.sequence_double

def sequence_halve(seq):
    return _libcvht.sequence_halve(seq)
sequence_halve = _libcvht.sequence_halve

def sequence_set_trg_playmode(seq, v):
    return _libcvht.sequence_set_trg_playmode(seq, v)
sequence_set_trg_playmode = _libcvht.sequence_set_trg_playmode

def sequence_set_trg_quantise(seq, v):
    return _libcvht.sequence_set_trg_quantise(seq, v)
sequence_set_trg_quantise = _libcvht.sequence_set_trg_quantise

def sequence_get_trg_playmode(seq):
    return _libcvht.sequence_get_trg_playmode(seq)
sequence_get_trg_playmode = _libcvht.sequence_get_trg_playmode

def sequence_get_trg_quantise(seq):
    return _libcvht.sequence_get_trg_quantise(seq)
sequence_get_trg_quantise = _libcvht.sequence_get_trg_quantise

def sequence_set_trig(seq, t, tp, ch, nt):
    return _libcvht.sequence_set_trig(seq, t, tp, ch, nt)
sequence_set_trig = _libcvht.sequence_set_trig

def sequence_get_trig(seq, t):
    return _libcvht.sequence_get_trig(seq, t)
sequence_get_trig = _libcvht.sequence_get_trig

def sequence_trigger_mute(seq):
    return _libcvht.sequence_trigger_mute(seq)
sequence_trigger_mute = _libcvht.sequence_trigger_mute

def sequence_trigger_cue(seq):
    return _libcvht.sequence_trigger_cue(seq)
sequence_trigger_cue = _libcvht.sequence_trigger_cue

def sequence_trigger_play_on(seq):
    return _libcvht.sequence_trigger_play_on(seq)
sequence_trigger_play_on = _libcvht.sequence_trigger_play_on

def sequence_trigger_play_off(seq):
    return _libcvht.sequence_trigger_play_off(seq)
sequence_trigger_play_off = _libcvht.sequence_trigger_play_off

def sequence_get_playing(seq):
    return _libcvht.sequence_get_playing(seq)
sequence_get_playing = _libcvht.sequence_get_playing

def sequence_set_playing(seq, p):
    return _libcvht.sequence_set_playing(seq, p)
sequence_set_playing = _libcvht.sequence_set_playing

def sequence_set_lost(seq, p):
    return _libcvht.sequence_set_lost(seq, p)
sequence_set_lost = _libcvht.sequence_set_lost

def sequence_get_rpb(seq):
    return _libcvht.sequence_get_rpb(seq)
sequence_get_rpb = _libcvht.sequence_get_rpb

def sequence_set_rpb(seq, rpb):
    return _libcvht.sequence_set_rpb(seq, rpb)
sequence_set_rpb = _libcvht.sequence_set_rpb

def sequence_get_cue(seq):
    return _libcvht.sequence_get_cue(seq)
sequence_get_cue = _libcvht.sequence_get_cue

def sequence_clone(seq):
    return _libcvht.sequence_clone(seq)
sequence_clone = _libcvht.sequence_clone

def track_get_row_ptr(arg1, c, r):
    return _libcvht.track_get_row_ptr(arg1, c, r)
track_get_row_ptr = _libcvht.track_get_row_ptr

def track_get_ctrlrow_ptr(arg1, c, r):
    return _libcvht.track_get_ctrlrow_ptr(arg1, c, r)
track_get_ctrlrow_ptr = _libcvht.track_get_ctrlrow_ptr

def track_get_index(trk):
    return _libcvht.track_get_index(trk)
track_get_index = _libcvht.track_get_index

def track_get_length(trk):
    return _libcvht.track_get_length(trk)
track_get_length = _libcvht.track_get_length

def track_get_ncols(trk):
    return _libcvht.track_get_ncols(trk)
track_get_ncols = _libcvht.track_get_ncols

def track_get_port(trk):
    return _libcvht.track_get_port(trk)
track_get_port = _libcvht.track_get_port

def track_get_channel(trk):
    return _libcvht.track_get_channel(trk)
track_get_channel = _libcvht.track_get_channel

def track_get_nrows(trk):
    return _libcvht.track_get_nrows(trk)
track_get_nrows = _libcvht.track_get_nrows

def track_get_nsrows(trk):
    return _libcvht.track_get_nsrows(trk)
track_get_nsrows = _libcvht.track_get_nsrows

def track_get_playing(trk):
    return _libcvht.track_get_playing(trk)
track_get_playing = _libcvht.track_get_playing

def track_get_pos(trk):
    return _libcvht.track_get_pos(trk)
track_get_pos = _libcvht.track_get_pos

def track_set_port(trk, n):
    return _libcvht.track_set_port(trk, n)
track_set_port = _libcvht.track_set_port

def track_set_channel(trk, n):
    return _libcvht.track_set_channel(trk, n)
track_set_channel = _libcvht.track_set_channel

def track_set_nrows(trk, n):
    return _libcvht.track_set_nrows(trk, n)
track_set_nrows = _libcvht.track_set_nrows

def track_set_nsrows(trk, n):
    return _libcvht.track_set_nsrows(trk, n)
track_set_nsrows = _libcvht.track_set_nsrows

def track_set_playing(trk, p):
    return _libcvht.track_set_playing(trk, p)
track_set_playing = _libcvht.track_set_playing

def track_add_ctrl(trk, ctl):
    return _libcvht.track_add_ctrl(trk, ctl)
track_add_ctrl = _libcvht.track_add_ctrl

def track_del_ctrl(trk, c):
    return _libcvht.track_del_ctrl(trk, c)
track_del_ctrl = _libcvht.track_del_ctrl

def track_swap_ctrl(trk, c, c2):
    return _libcvht.track_swap_ctrl(trk, c, c2)
track_swap_ctrl = _libcvht.track_swap_ctrl

def track_set_ctrl(trk, c, n, val):
    return _libcvht.track_set_ctrl(trk, c, n, val)
track_set_ctrl = _libcvht.track_set_ctrl

def track_get_ctrl(tkl, ret, l, c, n):
    return _libcvht.track_get_ctrl(tkl, ret, l, c, n)
track_get_ctrl = _libcvht.track_get_ctrl

def track_get_ctrl_rec(tkl, ret, l, c, n):
    return _libcvht.track_get_ctrl_rec(tkl, ret, l, c, n)
track_get_ctrl_rec = _libcvht.track_get_ctrl_rec

def track_get_ctrl_env(tkl, ret, l, c, n):
    return _libcvht.track_get_ctrl_env(tkl, ret, l, c, n)
track_get_ctrl_env = _libcvht.track_get_ctrl_env

def track_get_ctrl_nums(trk):
    return _libcvht.track_get_ctrl_nums(trk)
track_get_ctrl_nums = _libcvht.track_get_ctrl_nums

def track_set_ctrl_num(trk, c, v):
    return _libcvht.track_set_ctrl_num(trk, c, v)
track_set_ctrl_num = _libcvht.track_set_ctrl_num

def track_get_lctrlval(trk, c):
    return _libcvht.track_get_lctrlval(trk, c)
track_get_lctrlval = _libcvht.track_get_lctrlval

def track_ctrl_refresh_envelope(trk, c):
    return _libcvht.track_ctrl_refresh_envelope(trk, c)
track_ctrl_refresh_envelope = _libcvht.track_ctrl_refresh_envelope

def track_get_nctrl(trk):
    return _libcvht.track_get_nctrl(trk)
track_get_nctrl = _libcvht.track_get_nctrl

def track_get_ctrlpr(trk):
    return _libcvht.track_get_ctrlpr(trk)
track_get_ctrlpr = _libcvht.track_get_ctrlpr

def track_get_envelope(trk, c):
    return _libcvht.track_get_envelope(trk, c)
track_get_envelope = _libcvht.track_get_envelope

def track_add_col(trk):
    return _libcvht.track_add_col(trk)
track_add_col = _libcvht.track_add_col

def track_del_col(trk, c):
    return _libcvht.track_del_col(trk, c)
track_del_col = _libcvht.track_del_col

def track_swap_col(trk, c, c2):
    return _libcvht.track_swap_col(trk, c, c2)
track_swap_col = _libcvht.track_swap_col

def track_resize(trk, size):
    return _libcvht.track_resize(trk, size)
track_resize = _libcvht.track_resize

def track_double(trk):
    return _libcvht.track_double(trk)
track_double = _libcvht.track_double

def track_halve(trk):
    return _libcvht.track_halve(trk)
track_halve = _libcvht.track_halve

def track_trigger(trk):
    return _libcvht.track_trigger(trk)
track_trigger = _libcvht.track_trigger

def track_kill_notes(trk):
    return _libcvht.track_kill_notes(trk)
track_kill_notes = _libcvht.track_kill_notes

def track_set_program(trk, p):
    return _libcvht.track_set_program(trk, p)
track_set_program = _libcvht.track_set_program

def track_set_bank(trk, msb, lsb):
    return _libcvht.track_set_bank(trk, msb, lsb)
track_set_bank = _libcvht.track_set_bank

def track_get_program(trk):
    return _libcvht.track_get_program(trk)
track_get_program = _libcvht.track_get_program

def track_set_qc1(trk, ctrl, val):
    return _libcvht.track_set_qc1(trk, ctrl, val)
track_set_qc1 = _libcvht.track_set_qc1

def track_set_qc2(trk, ctrl, val):
    return _libcvht.track_set_qc2(trk, ctrl, val)
track_set_qc2 = _libcvht.track_set_qc2

def track_get_qc(trk):
    return _libcvht.track_get_qc(trk)
track_get_qc = _libcvht.track_get_qc

def track_set_loop(trk, v):
    return _libcvht.track_set_loop(trk, v)
track_set_loop = _libcvht.track_set_loop

def track_get_loop(trk):
    return _libcvht.track_get_loop(trk)
track_get_loop = _libcvht.track_get_loop

def track_get_indicators(trk):
    return _libcvht.track_get_indicators(trk)
track_get_indicators = _libcvht.track_get_indicators

def track_set_indicators(trk, i):
    return _libcvht.track_set_indicators(trk, i)
track_set_indicators = _libcvht.track_set_indicators

def track_new(port, channel, len, songlen, ctrlpr):
    return _libcvht.track_new(port, channel, len, songlen, ctrlpr)
track_new = _libcvht.track_new

def row_get_type(rw):
    return _libcvht.row_get_type(rw)
row_get_type = _libcvht.row_get_type

def row_get_note(rw):
    return _libcvht.row_get_note(rw)
row_get_note = _libcvht.row_get_note

def row_get_velocity(rw):
    return _libcvht.row_get_velocity(rw)
row_get_velocity = _libcvht.row_get_velocity

def row_get_delay(rw):
    return _libcvht.row_get_delay(rw)
row_get_delay = _libcvht.row_get_delay

def row_set_type(rw, type):
    return _libcvht.row_set_type(rw, type)
row_set_type = _libcvht.row_set_type

def row_set_note(rw, note):
    return _libcvht.row_set_note(rw, note)
row_set_note = _libcvht.row_set_note

def row_set_velocity(rw, velocity):
    return _libcvht.row_set_velocity(rw, velocity)
row_set_velocity = _libcvht.row_set_velocity

def row_set_delay(rw, delay):
    return _libcvht.row_set_delay(rw, delay)
row_set_delay = _libcvht.row_set_delay

def row_set(rw, type, note, velocity, delay):
    return _libcvht.row_set(rw, type, note, velocity, delay)
row_set = _libcvht.row_set

def ctrlrow_get_velocity(crw):
    return _libcvht.ctrlrow_get_velocity(crw)
ctrlrow_get_velocity = _libcvht.ctrlrow_get_velocity

def ctrlrow_get_linked(crw):
    return _libcvht.ctrlrow_get_linked(crw)
ctrlrow_get_linked = _libcvht.ctrlrow_get_linked

def ctrlrow_get_smooth(crw):
    return _libcvht.ctrlrow_get_smooth(crw)
ctrlrow_get_smooth = _libcvht.ctrlrow_get_smooth

def ctrlrow_get_anchor(crw):
    return _libcvht.ctrlrow_get_anchor(crw)
ctrlrow_get_anchor = _libcvht.ctrlrow_get_anchor

def ctrlrow_set_velocity(crw, v):
    return _libcvht.ctrlrow_set_velocity(crw, v)
ctrlrow_set_velocity = _libcvht.ctrlrow_set_velocity

def ctrlrow_set_linked(crw, l):
    return _libcvht.ctrlrow_set_linked(crw, l)
ctrlrow_set_linked = _libcvht.ctrlrow_set_linked

def ctrlrow_set_smooth(crw, s):
    return _libcvht.ctrlrow_set_smooth(crw, s)
ctrlrow_set_smooth = _libcvht.ctrlrow_set_smooth

def ctrlrow_set_anchor(crw, a):
    return _libcvht.ctrlrow_set_anchor(crw, a)
ctrlrow_set_anchor = _libcvht.ctrlrow_set_anchor

def ctrlrow_set(crw, v, l, s, a):
    return _libcvht.ctrlrow_set(crw, v, l, s, a)
ctrlrow_set = _libcvht.ctrlrow_set

def timeline_change_set(tl, row, bpm, linked):
    return _libcvht.timeline_change_set(tl, row, bpm, linked)
timeline_change_set = _libcvht.timeline_change_set

def timeline_change_del(tl, id):
    return _libcvht.timeline_change_del(tl, id)
timeline_change_del = _libcvht.timeline_change_del

def timeline_get_change(tl, id):
    return _libcvht.timeline_get_change(tl, id)
timeline_get_change = _libcvht.timeline_get_change

def timeline_get_nchanges(tl):
    return _libcvht.timeline_get_nchanges(tl)
timeline_get_nchanges = _libcvht.timeline_get_nchanges

def timeline_get_nticks(tl):
    return _libcvht.timeline_get_nticks(tl)
timeline_get_nticks = _libcvht.timeline_get_nticks

def timeline_get_tick(tl, n):
    return _libcvht.timeline_get_tick(tl, n)
timeline_get_tick = _libcvht.timeline_get_tick

def timeline_get_strip(tl, n):
    return _libcvht.timeline_get_strip(tl, n)
timeline_get_strip = _libcvht.timeline_get_strip

def timeline_get_nstrips(tl):
    return _libcvht.timeline_get_nstrips(tl)
timeline_get_nstrips = _libcvht.timeline_get_nstrips

def timeline_add_strip(tl, seq, start, length, rpb_start, rpb_end, loop_length):
    return _libcvht.timeline_add_strip(tl, seq, start, length, rpb_start, rpb_end, loop_length)
timeline_add_strip = _libcvht.timeline_add_strip

def timeline_del_strip(tl, id):
    return _libcvht.timeline_del_strip(tl, id)
timeline_del_strip = _libcvht.timeline_del_strip

def timestrip_get_seq_id(tstr):
    return _libcvht.timestrip_get_seq_id(tstr)
timestrip_get_seq_id = _libcvht.timestrip_get_seq_id

def timestrip_get_start(tstr):
    return _libcvht.timestrip_get_start(tstr)
timestrip_get_start = _libcvht.timestrip_get_start

def timestrip_get_length(tstr):
    return _libcvht.timestrip_get_length(tstr)
timestrip_get_length = _libcvht.timestrip_get_length

def timestrip_get_rpb_start(tstr):
    return _libcvht.timestrip_get_rpb_start(tstr)
timestrip_get_rpb_start = _libcvht.timestrip_get_rpb_start

def timestrip_get_rpb_end(tstr):
    return _libcvht.timestrip_get_rpb_end(tstr)
timestrip_get_rpb_end = _libcvht.timestrip_get_rpb_end

def timestrip_get_loop_length(tstr):
    return _libcvht.timestrip_get_loop_length(tstr)
timestrip_get_loop_length = _libcvht.timestrip_get_loop_length

def timestrip_set_start(tstr, start):
    return _libcvht.timestrip_set_start(tstr, start)
timestrip_set_start = _libcvht.timestrip_set_start

def timestrip_set_length(tstr, length):
    return _libcvht.timestrip_set_length(tstr, length)
timestrip_set_length = _libcvht.timestrip_set_length

def timestrip_set_rpb_start(tstr, rpb_start):
    return _libcvht.timestrip_set_rpb_start(tstr, rpb_start)
timestrip_set_rpb_start = _libcvht.timestrip_set_rpb_start

def timestrip_set_rpb_end(tstr, rpb_end):
    return _libcvht.timestrip_set_rpb_end(tstr, rpb_end)
timestrip_set_rpb_end = _libcvht.timestrip_set_rpb_end

def timestrip_set_loop_length(tstr, loop_length):
    return _libcvht.timestrip_set_loop_length(tstr, loop_length)
timestrip_set_loop_length = _libcvht.timestrip_set_loop_length

def parse_note(arg1):
    return _libcvht.parse_note(arg1)
parse_note = _libcvht.parse_note
# This file is compatible with both classic and new-style classes.


