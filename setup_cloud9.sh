#!/bin/bash

sudo apt-get install -y sendxmpp python-pexpect python-googleapi python-lockfile python-tz python-dateutil
# sudo apt-get install -y libroot-core-dev libroot-math-physics-dev libroot-graf2d-postscript-dev libroot-bindings-python-dev
# sudo apt-get install -y x11vnc novnc fluxbox vnc4server
scp ddboline@ddbolineathome.mooo.com:~/setup_files/build/ddboline_personal_scripts/*.dat .

sh test_cloud9.sh
