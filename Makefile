#Poor Man's Sequencer by Remigiusz Dybka

# change these two to suit your stuff
PYTHON_INCLUDE=/usr/include/python3.6m
INST_DIR=$(HOME)/.local

CC=gcc
CFLAGS=-I$(PYTHON_INCLUDE) -fPIC
LIBS=-lm -ljack
DEPS=libvht/libvht.h \
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
	libvht/libvht.o \
	libvht/module.o \
	libvht/sequence.o \
	libvht/track.o \
	libvht/row.o 

all: libvht/_libcvht.so

%.o: %c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

libvht/libvht_wrap.c: $(DEPS) $(OBJ)
	swig -python libvht/libvht.h

libvht/vht_wrap.o: libvht/libvht_wrap.c
	$(CC) -c -o $@ $< $(CFLAGS)

libvht/_libcvht.so: $(OBJ) libvht/libvht_wrap.o libvht/libcvht.py
	ld -shared $(OBJ) libvht/libvht_wrap.o -o $@ $(LIBS)

install: libvht/_libcvht.so
	mkdir -p $(INST_DIR)/share/vht/libvht 
	cp -r dist/* $(INST_DIR)
	cp vht $(INST_DIR)/bin
	cp -r libvht/* $(INST_DIR)/share/vht/libvht
	cp -r src/*.py $(INST_DIR)/share/vht
		
clean:
	rm -f *.so *.o libvht/libvht.py libvht/*.so
	rm -f libvht/*.o libvht/libvht_wrap.c
	rm -rf src/__pycache__
	rm -rf libvht/__pycache__
	rm -rf libvht/*.pyc
	rm -rf src/*.pyc
	
	
