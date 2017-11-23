#!/bin/sh
astyle -A14 lib/*.c lib/*.h

# pms.h needs special treatment
rm vhtlib/libpms.h
mv vhtlib/libpms.h.orig vhtlib/libpms.h

rm vhtlib/*.orig
