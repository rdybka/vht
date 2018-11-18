#!/bin/sh

mv libvht.h libvht.g
astyle -A14 --indent=tab *.c *.h
mv libvht.g libvht.h
rm *.orig
