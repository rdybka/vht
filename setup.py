#!/usr/bin/env python3

from setuptools import setup, Extension

setup(name = "vht",
	version = "0.1.8",
	description = "Valhalla MIDI Tracker",
	author = "Remigiusz Dybka",
	author_email = "remigiusz.dybka@gmail.com",
	url = "https://github.com/rdybka/vht",
	license = 'GPLv3+',
	ext_modules = [Extension("_libcvht", ["libcvht/libvht.c",
			"libcvht/libcvht_wrap.c",
			"libcvht/midi_client.c",
			"libcvht/jack_process.c",
			"libcvht/midi_event.c",
			"libcvht/module.c",
			"libcvht/row.c",
			"libcvht/ctrlrow.c",
			"libcvht/sequence.c",
			"libcvht/track.c",
			"libcvht/envelope.c",
			"libcvht/timeline.c"], 
			libraries = ["jack"])],

	packages = ["vht", "libvht"],
	entry_points={
        'console_scripts': [
            'vht = vht.main:run',
        ]},
	
	data_files = [
		('share/vht', ['data/vht.svg', 'data/vht.png', 'data/menu.ui', 'data/ctrl/10-gm', 'data/ctrl/20-zyn', 'data/bank/10-gm1', 'data/bank/20-gm2']),
		('share/icons', ['data/vht.svg']),
		('share/applications', ['data/com.github.rdybka.vht.desktop'])
	],
	
	classifiers=[
		'Environment :: X11 Applications :: Gnome',
		'Development Status :: 2 - Pre-Alpha',
		'Intended Audience :: End Users/Desktop',
		'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
		'Programming Language :: Python :: 3',
		'Programming Language :: C',
		'Topic :: Multimedia :: Sound/Audio :: MIDI'
	]
)
