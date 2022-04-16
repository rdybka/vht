![vht header](/data/vht_header.png)
## about
vahatraker is a MIDI sequencing companion
for GNU/Linux audio setups. Adhering to Unix philosophy,
it tries to do one thing well, which in it's instance boils
down to providing a tool of expression that:

- doesn't make a sound
- relies 100% on JACK
- has fast workflow
- unheard of time signatures
- fractal turtles
- ridiculous, accurate BPM
- scenes a'la 'ton

## dependencies
```
fedora - python3-devel jack-audio-connection-kit-devel jack_capture
ubuntu - build-essential python3-dev python3-setuptools libjack-jackd2-dev jack-capture
```

## install
```
./setup.py install --user
```
