#!/usr/bin/env bash

# Exit on error, run verbose
set -euvo pipefail

# Run from a script to make sure Travis CI handles failures properly:
# http://steven.casagrande.io/articles/travis-ci-and-if-statements/

if   [ $TRAVIS_PYTHON_VERSION == 2.6 ]; then python 2.6/get-pip.py;
elif [ $TRAVIS_PYTHON_VERSION == 3.2 ]; then python 3.2/get-pip.py;
elif [ $TRAVIS_PYTHON_VERSION == 3.3 ]; then python 3.3/get-pip.py;
else                                         python get-pip.py;
fi

exit 0;
