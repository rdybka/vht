#include "jack_client.h"

#include "pms.h"

int start() {
	return jack_start();
}

void stop() {
	jack_stop();
}
