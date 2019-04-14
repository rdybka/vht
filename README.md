![vht header](/data/vht_header.png)
## about
Valhalla Tracker aims to be a MIDI sequencing companion for your
JACK/Yoshimi/Hydrogen/Calf setup. It relies 100% on JACK for timing
which allows sample-exact synchronisation and in future, 
asynchronous rendering.

## installation (tested on Fedora 29 and Ubuntu 18.10)
```
[fedora] dnf install python3-devel jack-audio-connection-kit-devel
[ubuntu] 

pip3 install vht --user
```

## roadmap before a file release
- [x] record/edit notes
- [x] record/edit controllers
- [x] console
- [ ] timeline
- [ ] loops
- [ ] triggers
- [ ] export midi/wav
- [ ] configuration window

deadline: soon enough
