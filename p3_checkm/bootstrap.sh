#!/usr/bin/env bash

target=${TARGET-/usr/local}

if [[ $# -ne 0 ]] ; then
        target=$1
        shift
fi

$target/bin/pip install --install-option="--prefix=$target" checkm-genome

exit

