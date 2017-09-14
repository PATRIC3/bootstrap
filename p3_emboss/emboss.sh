#!/usr/bin/env bash

target=${TARGET-/usr/local}

if [[ $# -ne 0 ]] ; then
        target=$1
        shift
fi

# user will need to set LD_LIBRARY_PATH
# export LD_LIBRARY_PATH=$target/lib:$LD_LIBRARY_PATH


wget ftp://emboss.open-bio.org/pub/EMBOSS/EMBOSS-6.6.0.tar.gz
tar -xvzf EMBOSS-6.6.0.tar.gz 

mkdir -p $target
mkdir -p $target/bin
mkdir -p $target/lib

cd EMBOSS-6.6.0

./configure --prefix=$target
make
make install

cd ..

