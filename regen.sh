#!/bin/sh

# - clears the tree,
# - regenerates the wrapper for libvht
# - don't run without swig4 installed
# - also uses black, astyle and pandoc

rm -f log.txt
rm -f *.so *.o
rm -f libvht/*.o
rm rf -f install.txt
rm -rf __pycache__
rm -rf vht/__pycache__
rm -rf libvht/__pycache__
rm -rf build
rm -rf deb_dist
rm -f dist/*.gz
rm -f MANIFEST
rm -rf libvht/*.pyc
rm -rf vht/*.pyc
rm -rf dist
rm -rf vht.egg-info
#rm -f libvht/libcvht_wrap.c

#cd libvht
#./beautify.sh
#cd ..
#black vht/*.py libvht/*.py
#swig -python libvht/libcvht.h
rm doc/vht.1.gz
pandoc doc/vht.1.md -s -t man -o doc/vht.1
gzip doc/vht.1
#git add .
#git reset libvht/*.so
