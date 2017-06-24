#include <stdio.h>
#include "jack_client.h"
#include "jack_process.h"

#include "pms.h"

int start() {
	return jack_start();
}

void stop() {
	jack_stop();
}

int get_passthrough()
{
	return passthrough;
}

void set_passthrough(int val)
{
	passthrough = val;
}
