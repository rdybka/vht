#!/usr/bin/env python3

from distutils.core import setup, Extension

setup(name = "vht",
	version = "0.1.3",
	description = "Valhalla JACK MIDI Tracker",
	author = "Remigiusz Dybka",
	author_email = "remigiusz.dybka@gmail.com",
	url = "https://github.com/rdybka/vht",
	ext_modules = [Extension("_libcvht", ["libvht/libvht.c",
			"libvht/libvht_wrap.c",
			"libvht/jack_client.c",
			"libvht/jack_process.c",
			"libvht/midi_event.c",
			"libvht/module.c",
			"libvht/pmp.c",
			"libvht/row.c",
			"libvht/sequence.c",
			"libvht/track.c"], 
			libraries = ["jack"])],
	packages = ["libvht"]
)
