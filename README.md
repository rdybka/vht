![vht header](/data/vht_header.png)
## about
Valhalla Tracker aims to be a MIDI sequencing companion
for GNU/Linux audio setups. Adhering to Unix philosophy,
it tries to do one thing well

- by itself produces no sound and won't run on Windows™
- timing/input/output relies 100% on JACK
- seems to work fine with fluidsynth, ZynAddSubFX and a MIDI controller
- probably most suitable for loop based music
- minimalistic by design
- minimalistic by necessity
- can save and load files
- sparsely documented for hacking pleasure

## in zip
- C library which talks to JACK and runs gameloop
- it's Python counterpart, lazily wrapped with SWIG
- GTK human interface also written in snake language

## deps
```
fedora - python3-devel jack-audio-connection-kit-devel
ubuntu - python3-dev libjack-jackd2-dev

and the usual GNOME stuff
```

## install
```
pip3 install vht
```
