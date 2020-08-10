#!/bin/bash
set -x

NETBOX_VERSION="v2.8.7"

EXIT=0

# Check all files for syntax errors
# Syntax check all python source files
SYNTAX=$(find . -name "*.py" -type f -exec python -m py_compile {} \; 2>&1)
if [[ ! -z $SYNTAX ]]; then
  echo ""
  echo "$SYNTAX"
  echo "Detected one or more syntax errors, failing build."
  EXIT=1
fi


# Check code conventions
flake8 --ignore W504,E501 netbox_sidekick/
RC=$?
if [[ $RC != 0 ]]; then
  echo ""
  echo "Detected one or more flake8 errors, failing build."
  EXIT=1
fi

# Install NetBox
mkdir build
cd build
git clone https://github.com/netbox-community/netbox
cd netbox
git checkout $NETBOX_VERSION
pip install -r requirements.txt 2>&1 > /dev/null
cd ../..

# Install netbox_sidekick
python setup.py develop

cp scripts/configuration.testing.py build/netbox/netbox/netbox/configuration.py

# Run netbox_sidekick unit tests
cd build/netbox
coverage run --source="netbox/" netbox/manage.py test netbox_sidekick
RC=$?
if [[ $RC != 0 ]]; then
  echo ""
  echo "Detected one or more failing tests, failing build."
  EXIT=1
fi

exit $EXIT
