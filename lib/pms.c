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

int get_bpm() {
    return module.bpm;
}

void set_bpm(int bpm) {
    module.bpm = bpm;
}

int get_nseq(void) {
    return module.nseq;
}

void module_play(int play) {
    module.playing = play;
}

int module_is_playing() {
    return module.playing;
}

void module_reset() {
    module.seq[0]->pos = 0;
    for (int t = 0; t < module.seq[0]->ntrk; t++)
        track_reset(module.seq[0]->trk[t]);
}

