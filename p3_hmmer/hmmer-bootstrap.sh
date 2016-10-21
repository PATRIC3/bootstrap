#!/usr/bin/env bash

target=${TARGET-/usr/local}

if [[ $# -ne 0 ]] ; then
        target=$1
        shift
fi

BUILD_TOOLS=${BUILD_TOOLS-/disks/patric-common/runtime/gcc-4.9.3}
export PATH=$BUILD_TOOLS/bin:$PATH

rm -r hmmer-3.1b2*

wget http://eddylab.org/software/hmmer3/3.1b2/hmmer-3.1b2.tar.gz
tar -xvzf hmmer-3.1b2.tar.gz
pushd hmmer-3.1b2

./configure --prefix=$target
make
make check
make install
popd
