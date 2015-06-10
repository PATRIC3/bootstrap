#!/bin/bash

target=${TARGET-/kb/runtime}

wget --no-check-certificate -P ${target}/bin https://github.com/aswarren/Prok-tuxedo/raw/master/prok_tuxedo.py
chmod a+x ${target}/bin/prok_tuxedo.py


