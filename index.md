![vht header](vht_header.png)
## about
Valhalla Tracker aims to be a MIDI sequencing companion
for GNU/Linux audio setups. Adhering to Unix philosophy,
it tries to do one thing well

- input/output relies 100% on JACK
- which allows for sample exact timing
- and freewheel rendering
- fits well between a MIDI controller and Carla/fluidsynth/Zyn
- fast workflow with lots of keyboard shortcuts
- allows for "unheard of" time signatures
- starts in one second, builds in five
- fits on a floppy

The sequencing engine is written in C, has a Python library on top
of it, which can be used headless (for generative composition or whatever).
The GUI is also written in Python and uses GTK through GObject Introspection.

## dependencies
```
fedora - python3-devel jack-audio-connection-kit-devel jack_capture
ubuntu - build-essential python3-dev python3-setuptools libjack-jackd2-dev jack-capture
```

## install
```
./setup.py install --user
```

