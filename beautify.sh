#!/bin/sh
astyle -A14 lib/*.c lib/*.h

# pms.h needs special treatment
rm lib/libpms.h
mv lib/libpms.h.orig lib/libpms.h

rm lib/*.orig
