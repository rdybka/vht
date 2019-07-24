![vht header](/data/vht_header.png)
## about
Valhalla Tracker is a MIDI sequencing companion for
your GNU/Linux audio setup

- by itself produces no sound and will not run on Windows
- timing/input/output relies 100% on JACK
- motivated by ability to mess with time
- probably most suitable for loop based music
- seems to work fine with ZynAddSubFX and a MIDI keyboard
- that's the only way it's been tested
- minimalistic by design
- minimalistic by necessity
- open-sourced in case someone finds it useful
- tries not to interfere
- but inspire
- for the same reason, sparsely documented

## in zip
- C library which talks to JACK and runs gameloop
- GTK interface written in Python

## deps
```
fedora - python3-devel jack-audio-connection-kit-devel
ubuntu - python3-dev libjack-jackd2-dev
```

## roadmap before a file release
- [x] record/edit notes
- [x] record/edit controllers
- [x] console
- [ ] triggers
- [ ] timeline
- [ ] export midi/wav
- [ ] configuration window

deadline: soon enough
