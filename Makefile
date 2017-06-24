#Poor Man's Sequencer by Remigiusz Dybka

PYTHON_INCLUDE=/usr/include/python3.5m
CC=gcc
CFLAGS=-I$(PYTHON_INCLUDE) -fPIC
LIBS=-lm -ljack
DEPS=pms.h \
	jack_client.h \
	jack_process.h \
	midi_event.h 
	
OBJ=jack_client.o jack_process.o midi_event.o pms.o

all: _pms.so

%.o: %c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

pms_wrap.c: $(DEPS) $(OBJ)
	swig -python pms.h

pms_wrap.o: pms_wrap.c
	$(CC) -c -o $@ $< $(CFLAGS)

_pms.so: $(OBJ) pms_wrap.o
	ld -shared $(OBJ) pms_wrap.o -o $@ $(LIBS)
		
clean:
	rm -f *.so *.o pms_wrap.c
	rm -rf __pycache__	
