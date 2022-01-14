![vht header](/data/vht_header.png)
## about
vahatraker is a MIDI sequencing companion
for GNU/Linux audio setups. Adhering to Unix philosophy,
it tries to do one thing well, which in it's instance boils
down to providing a tool of expression that:

- relies 100% on JACK for input/output
- ...which allows sample exact timing
- ...and freewheel rendering
- has a fast workflow with a splendid selection of keyboard shortcuts 
- doesn't make a sound
- is built for live editing/performance
- has scenes a'la 'ton
- fractal turtles
- allows ridiculous, yet accurate BPM
- and unheard of time signatures

The sequencing engine is written in C, has a Python library on top
of it, which can be used headless for generative composition, or whatevs
or if you don't like the GUI which also was dearly written in the
language we shall no longer spam about, relies on GTK through GObject Introspection.
And Linux.

## dependencies
```
fedora - python3-devel jack-audio-connection-kit-devel jack_capture
ubuntu - build-essential python3-dev python3-setuptools libjack-jackd2-dev jack-capture
```

## install
```
./setup.py install --user
```
