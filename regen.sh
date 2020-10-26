#!/bin/sh

# - clears the tree so we can do "git add ." (I know, I know)
# - regenerates the wrapper for libvht
# - don't run without swig4 installed
# - also uses black and astyle

rm -f log.txt
rm -f *.so *.o
rm -f libvht/*.o
rm rf -f install.txt
rm -rf __pycache__
rm -rf vht/__pycache__
rm -rf libvht/__pycache__
rm -rf build
rm -f dist/*.gz
rm -f MANIFEST
rm -rf libvht/*.pyc
rm -rf vht/*.pyc
rm -rf dist
rm -rf vht.egg-info
rm -f libvht/libcvht_wrap.c

cd libvht
./beautify.sh
cd ..
black vht/*.py libvht/*.py
swig -python libvht/libcvht.h
git add .
git reset libvht/*.so

