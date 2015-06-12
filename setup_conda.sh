#!/bin/bash

sudo /opt/conda/bin/conda install --yes pip pytz dateutil

sudo /opt/conda/bin/conda install -c https://conda.binstar.org/ddboline --yes google-api-python-client

# sudo apt-get install -y python-googleapi python-tz python-dateutil
# sudo apt-get install -y python3-googleapi python3-tz python3-dateutil
scp ddboline@ddbolineathome.mooo.com:~/setup_files/build/ddboline_personal_scripts/client_secrets.json .
scp ddboline@ddbolineathome.mooo.com:~/setup_files/build/ddboline_personal_scripts/*.dat .
