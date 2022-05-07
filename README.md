![vht header](/data/vht_header.png)
## about
vahatraker is a MIDI sequencing companion
for GNU/Linux audio setups. Adhering to Unix philosophy,
it tries to do one thing well, which is to drive MIDI,
adhering to other doctrines, it tries to enable expression,
with added value of:

- live editing
- fast workflow
- intuitive midi-in
- unheard of time signatures
- fractal turtles
- scenes a'la 'ton

Frankly speaking, vht was envisaged to replace seq24 in author's "studio"
and offers similar functionality (and limitations) with a different approach
in places. It relies 100% on JACK audio connection kit for input/output/synch
and uses jack_capture for rendering. The GUI has similar dependencies
as gnome-calculator, tracker paradigm was chosen to allow for
rhythmic gymnastics otherwise hard to convey and because it's fun.

Low level stuff was done in C and wrapped in a Python library.
Monkeyterface employs GTK through gobject introspection and is also written
in the language we shall no longer spam about.

## dependencies
```
fedora - python3-devel jack-audio-connection-kit-devel jack_capture
ubuntu - build-essential python3-dev python3-setuptools libjack-jackd2-dev jack-capture
```

## install
```
./setup.py install --user
```
