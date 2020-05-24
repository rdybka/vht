#!/bin/sh

mv libcvht.h libcvht.g
astyle -A14 --indent=tab *.c *.h
mv libcvht.g libcvht.h
rm *.orig
