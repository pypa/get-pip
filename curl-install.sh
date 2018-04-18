#! /usr/bin/env bash

# Exit on error, run verbose
set -euvo pipefail

# Run from a script to make sure Travis CI handles failures properly:
# http://steven.casagrande.io/articles/travis-ci-and-if-statements/

if   [ $TRAVIS_PYTHON_VERSION == 2.6 ]; then curl https://bootstrap.pypa.io/2.6/get-pip.py | python
elif [ $TRAVIS_PYTHON_VERSION == 3.2 ]; then curl https://bootstrap.pypa.io/3.2/get-pip.py | python
elif [ $TRAVIS_PYTHON_VERSION == 3.3 ]; then curl https://bootstrap.pypa.io/3.3/get-pip.py | python
else                                         curl https://bootstrap.pypa.io/get-pip.py | python
fi

exit 0
