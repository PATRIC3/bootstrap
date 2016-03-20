#!/usr/bin/env bash

# set up for snpeff 

target=${TARGET-/usr/local}

if [[ $# -ne 0 ]] ; then
        target=$1
        shift
fi

dst=$target/data

# general steps:
# download latest
# unzip latest
# wrap jars and deploy as scripts
# configure location of database


# wget http://sourceforge.net/projects/snpeff/files/snpEff_latest_core.zip
# unzip snpEff_latest_core.zip

wget https://sourceforge.net/projects/snpeff/files/snpEff_v4_0_core.zip
unzip snpEff_v4_0_core.zip

cp -r snpEff $target 
pushd $target/snpEff

for n in *.jar ; do 
   p=$(basename $n .jar) ; 
   echo "\"java\" \"-jar\" \"$target/snpEff/$n\" \"\$@\"" > $target/bin/$p.sh ;
   chmod a+rx $target/bin/$p.sh ;
done

popd
