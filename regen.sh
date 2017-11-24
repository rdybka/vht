#!/bin/sh
# clears the tree so we can do "git add ." (I know, I know)
# and regenerates the wrapper for libvht

rm -f *.so *.o libvht/libmod.py libvht/*.so
rm -f libvht/*.o
rm -rf vht/__pycache__
rm -rf libvht/__pycache__
rm -rf build
rm -f dist/*.gz
rm -f MANIFEST
rm -rf libvht/*.pyc
rm -rf vht/*.pyc
rm -rf dist
rm -rf vht.egg-info
rm -f libvht/libvht_wrap.c

swig -python libvht/libvht.h
