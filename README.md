![vht header](/data/vht_header.png)
## about
Valhalla Tracker aims to be a MIDI sequencing companion
for GNU/Linux audio setups. Adhering to Unix philosophy,
it does one thing well.

- by itself produces no sound and won't run on Windows™
- timing/input/output relies 100% on JACK
- probably most suitable for loop based music
- seems to work fine with fluidsynth, ZynAddSubFX and a MIDI controller
- minimalistic by design
- minimalistic by necessity
- can load and save files
- tries not to interfere but inspire
- for the same reason, sparsely documented :]

## in zip
- C library which talks to JACK and runs gameloop
- GTK interface written in Python

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

## roadmap before a file release
- [x] record/edit notes
- [x] record/edit controllers
- [x] console
- [x] triggers
- [ ] timeline
- [ ] export midi/wav
- [ ] configuration window

deadline: soon enough
