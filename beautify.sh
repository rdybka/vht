#!/bin/sh
astyle -A14 lib/*.c lib/*.h

# pms.h needs special treatment
rm lib/pms.h
mv lib/pms.h.orig lib/pms.h

rm lib/*.orig
