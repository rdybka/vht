#!/usr/bin/env python3

from setuptools import setup, Extension

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name = "vht",
	version = "0.3.32",
	description = "vahatraker - a live MIDI sequencer for JACK",
	long_description=long_description,
	long_description_content_type="text/markdown",
	author = "Remigiusz Dybka",
	author_email = "remigiusz.dybka@gmail.com",
	url = "https://github.com/rdybka/vht",
	license = 'GPLv3+',
	ext_modules = [Extension("libvht/_libcvht", ["libvht/libvht.c",
			"libvht/libcvht_wrap.c",
			"libvht/midi_client.c",
			"libvht/jack_process.c",
			"libvht/midi_event.c",
			"libvht/module.c",
			"libvht/row.c",
			"libvht/ctrlrow.c",
			"libvht/sequence.c",
			"libvht/track.c",
			"libvht/envelope.c",
			"libvht/timeline.c",
			"libvht/mandy.c",
			"libvht/mandy_trk_disp.c",
			"libvht/mandy_pix_scan.c",
			"libvht/tracy.c"], 
			libraries = ["jack"])],

	packages = ["vht", "libvht"],
	entry_points={
		'console_scripts': [
		'vht = vht.main:run',
		]},
	
	data_files = [
		('share/vht', ['data/mandy.png', 'data/vht.svg', 'data/vht.png', 'data/menu.ui']),
		('share/vht/ctrl', ['data/ctrl/10-gm', 'data/ctrl/20-zyn']),
		('share/vht/bank', ['data/bank/10-gm1', 'data/bank/20-gm2']),
		('share/icons', ['data/vht.svg']),
		('share/man/man1', ['doc/vht.1.gz']),
		('share/applications', ['data/com.github.rdybka.vht.desktop'])
		
	],
	
	classifiers=[
		'Development Status :: 5 - Production/Stable',
		'Environment :: X11 Applications :: GTK',
		'Intended Audience :: End Users/Desktop',
		'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
		'Programming Language :: Python :: 3',
		'Programming Language :: C',
		'Operating System :: POSIX :: Linux',
		'Topic :: Multimedia :: Sound/Audio :: MIDI'
	]
)
