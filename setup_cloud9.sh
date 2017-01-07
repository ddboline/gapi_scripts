#!/bin/bash

export LANG="C.UTF-8"

#USERNAME=ddboline
#HOST=ddbolineathome.mooo.com
USERNAME=ubuntu
HOST=ddbolineinthecloud.mooo.com

sudo bash -c "echo deb ssh://${USERNAME}@${HOST}/var/www/html/deb/xenial/devel ./ > /etc/apt/sources.list.d/py2deb.list"

sudo apt-get update
sudo apt-get install -y --force-yes python-googleapi python-tz python-dateutil \
                                    python-requests python-pytest python-pytest-cov \
                                    python-setuptools python-dev python-bs4

scp ${USERNAME}@${HOST}:~/setup_files/build/ddboline_personal_scripts/client_secrets.json .
scp ${USERNAME}@${HOST}:~/setup_files/build/ddboline_personal_scripts/*.dat .
