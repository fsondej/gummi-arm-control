#!/usr/bin/env bash

# check os
uname_out=$(uname -s)
case ${uname_out} in
    Linux)      installer='sudo apt install' ;;
    Darwin)     installer='brew install' ;;
    *)          echo 'Your system is not supported, choose installer manually.'
                exit 1
esac

${installer} python3.6
${installer} python3.6-tk

# set up virtualenv
${installer} virtualenv
virtualenv -p python3.6 env
source env/bin/activate
pip install -r requirements.txt

wget https://raw.githubusercontent.com/FRC4564/maestro/master/maestro.py
mv maestro.py src/control/maestro.py

echo 'Installed successfully'

YELLOW='\033[0;31m'
echo -e "${YELLOW}Remember to set Pololu to 'USB Dual Port' serial mode"
