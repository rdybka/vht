#include <stdio.h>
#include "jack_client.h"
#include "jack_process.h"

#include "libpms.h"
#include "module.h"

int start() {
    return jack_start();
}

void stop() {
    jack_stop();
}

int module_get_bpm() {
    return module.bpm;
}

void module_set_bpm(int bpm) {
    module.bpm = bpm;
}

int get_nseq(void) {
    return module.nseq;
}

void module_play(int play) {
    module.playing = play;
    if (play == 0)
        module_mute();
}

int module_is_playing() {
    return module.playing;
}

void module_reset() {
    module.seq[0]->pos = 0;
    module.zero_time = 0;
    for (int t = 0; t < module.seq[0]->ntrk; t++)
        track_reset(module.seq[0]->trk[t]);
}

struct module_t *get_module() {
    return &module;
}

int module_get_nseq(void) {
    return module.nseq;
}

sequence *module_get_seq(int n) {
    return module.seq[n];
}
