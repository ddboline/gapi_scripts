#!/bin/bash

sudo apt-get install -y python-googleapi python-tz python-dateutil \
                        python-requests python-nose python-coverage \
                        python-setuptools python-dev python-bs4

scp ddboline@ddbolineathome.mooo.com:~/setup_files/build/ddboline_personal_scripts/client_secrets.json .
scp ddboline@ddbolineathome.mooo.com:~/setup_files/build/ddboline_personal_scripts/*.dat .
