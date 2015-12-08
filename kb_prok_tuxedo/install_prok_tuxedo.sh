#!/bin/bash

target=${TARGET-/kb/runtime}

#wget --no-check-certificate -P ${target}/bin https://github.com/aswarren/Prok-tuxedo/raw/master/prok_tuxedo.py
rm -rf Prok-tuxedo
git clone https://github.com/aswarren/Prok-tuxedo.git
cp Prok-tuxedo/prok_tuxedo.py ${target}/bin/
cp Prok-tuxedo/cuffdiff_to_genematrix.py ${target}/bin/

chmod a+x ${target}/bin/prok_tuxedo.py
chmod a+x ${target}/bin/cuffdiff_to_genematrix.py
