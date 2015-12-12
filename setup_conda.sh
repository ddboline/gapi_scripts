#!/bin/bash

sudo /opt/conda/bin/conda install -c https://conda.anaconda.org/ddboline --yes pytz python-dateutil google-api-python-client nose

# sudo apt-get install -y python-googleapi python-tz python-dateutil
# sudo apt-get install -y python3-googleapi python3-tz python3-dateutil
scp ddboline@ddbolineathome.mooo.com:~/setup_files/build/ddboline_personal_scripts/client_secrets.json .
scp ddboline@ddbolineathome.mooo.com:~/setup_files/build/ddboline_personal_scripts/*.dat .

### stupid stupid hack...
sudo chmod a+r /opt/conda/lib/python3*/site-packages/httplib2/cacerts.txt
