#Poor Man's Sequencer by Remigiusz Dybka

# change these two to suit your stuff
PYTHON_INCLUDE=/usr/include/python3.6m
INST_DIR=$(HOME)/.local

CC=gcc
CFLAGS=-I$(PYTHON_INCLUDE) -fPIC
LIBS=-lm -ljack
DEPS=lib/libpms.h \
	lib/jack_client.h \
	lib/jack_process.h \
	lib/midi_event.h \
	lib/row.h \
	lib/track.h \
	lib/module.h \
	lib/sequence.h 
	
OBJ=lib/jack_client.o \
	lib/jack_process.o \
	lib/midi_event.o \
	lib/libpms.o \
	lib/module.o \
	lib/sequence.o \
	lib/track.o \
	lib/row.o 

all: pypms/_libpms.so

%.o: %c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

lib/libpms_wrap.c: $(DEPS) $(OBJ)
	swig -python lib/libpms.h

lib/pms_wrap.o: lib/libpms_wrap.c
	$(CC) -c -o $@ $< $(CFLAGS)

pypms/libpms.py: lib/libpms_wrap.c
	cp lib/libpms.py pypms

pypms/_libpms.so: $(OBJ) lib/libpms_wrap.o pypms/libpms.py
	ld -shared $(OBJ) lib/libpms_wrap.o -o $@ $(LIBS)

install: pypms/_libpms.so
	mkdir -p $(INST_DIR)/share/pms/pypms 
	cp -r dist/* $(INST_DIR)
	cp pms $(INST_DIR)/bin
	cp -r pypms/* $(INST_DIR)/share/pms/pypms
	cp -r *.py $(INST_DIR)/share/pms
		
clean:
	rm -f *.so *.o lib/libpms.py pypms/libpms.py pypms/*.so
	rm -f lib/*.so lib/*.o lib/libpms_wrap.c
	rm -rf __pycache__
	rm -rf pypms/__pycache__
	rm -rf pypms/*.pyc
	
