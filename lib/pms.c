#include <stdio.h>
#include "jack_client.h"
#include "jack_process.h"

#include "pms.h"
#include "module.h"

int start() {
	module_new();
	return jack_start();
}

void stop() {
	jack_stop();
	module_free();
}

int get_passthrough()
{
	return passthrough;
}

void set_passthrough(int val)
{
	passthrough = val;
}

int get_bpm() {
	return module.bpm;
}

void set_bpm(int bpm) {
	module.bpm = bpm;
}

int get_nseq(void) {
	return module.nseq;
}


