#Poor Man's Sequencer by Remigiusz Dybka

# change these two to suit your stuff
PYTHON_INCLUDE=/usr/include/python3.6m
INST_DIR=$(HOME)/.local

CC=gcc
CFLAGS=-I$(PYTHON_INCLUDE) -fPIC
LIBS=-lm -ljack
DEPS=libvht/libmod.h \
	libvht/jack_client.h \
	libvht/jack_process.h \
	libvht/midi_event.h \
	libvht/row.h \
	libvht/track.h \
	libvht/module.h \
	libvht/sequence.h 
	
OBJ=libvht/jack_client.o \
	libvht/jack_process.o \
	libvht/midi_event.o \
	libvht/libmod.o \
	libvht/module.o \
	libvht/sequence.o \
	libvht/track.o \
	libvht/row.o 

all: libvht/_libcmod.so

%.o: %c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

libvht/libvht_wrap.c: $(DEPS) $(OBJ)
	swig -python libvht/libmod.h

libvht/vht_wrap.o: libvht/libvht_wrap.c
	$(CC) -c -o $@ $< $(CFLAGS)

libvht/_libcmod.so: $(OBJ) libvht/libvht_wrap.o libvht/libcmod.py
	ld -shared $(OBJ) libvht/libvht_wrap.o -o $@ $(LIBS)

install: libvht/_libcmod.so
	mkdir -p $(INST_DIR)/share/vht/libvht 
	cp -r dist/* $(INST_DIR)
	cp vht $(INST_DIR)/bin
	cp -r libvht/* $(INST_DIR)/share/vht/libvht
	cp -r vht/*.py $(INST_DIR)/share/vht
		
megaclean:
	rm libvht/libvht_wrap.c
	
clean:
	rm -f *.so *.o libvht/libmod.py libvht/*.so
	rm -f libvht/*.o
	rm -rf vht/__pycache__
	rm -rf libvht/__pycache__
	rm -rf build
	rm -f dist/*.gz
	rm -f MANIFEST
	rm -rf libvht/*.pyc
	rm -rf vht/*.pyc
	rm -rf dist
	rm -rf vht.egg-info
	
	
	
	
	
