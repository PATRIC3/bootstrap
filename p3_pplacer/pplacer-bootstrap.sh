#!/usr/bin/env bash
set -o verbose

# build script for pplacer 


target=${TARGET-/usr/local}

if [[ $# -ne 0 ]] ; then
        target=$1
        shift
fi


rm -r pplacer-Linux-v1.1.alpha18-2-gcb55169 pplacer-linux-v1.1.alpha18-2-gcb55169.zip
rm -r fhcrc-microbiome-demo-730d268


wget https://github.com/matsen/pplacer/releases/download/v1.1.alpha18/pplacer-linux-v1.1.alpha18-2-gcb55169.zip
unzip pplacer-linux-v1.1.alpha18-2-gcb55169.zip

mkdir -p $target/bin/
cp pplacer-*/guppy pplacer-*/pplacer pplacer-*/rppr $target/bin/


# test the install, just running a few cmds
wget http://github.com/fhcrc/microbiome-demo/zipball/master -O test-data.zip
unzip test-data.zip
TESTDIR=fhcrc-microbiome-demo-730d268

pushd $TESTDIR

$target/bin/pplacer -c vaginal_16s.refpkg src/p4z1r36.fasta
$target/bin/guppy fat -c vaginal_16s.refpkg p4z1r36.jplace
$target/bin/guppy kr src/*.jplace
$target/bin/guppy kr_heat -c vaginal_16s.refpkg/ src/p1z1r2.jplace src/p1z1r34.jplace
echo "tests passed"

popd


