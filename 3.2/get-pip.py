#!/usr/bin/env python
from __future__ import print_function
import sys
import textwrap

message = """
Hi there!

The URL you are using to fetch this script has changed, and this one will no
longer work. Please use get-pip.py from the following URL instead:

    https://bootstrap.pypa.io/pip/3.2/get-pip.py

Sorry if this change causes any inconvenience for you!

We don't have a good mechanism to make more gradual changes here, and this
renaming is a part of an effort to make it easier to us to update these
scripts, when there's a pip release. It's also essential for improving how we
handle the `get-pip.py` scripts, when pip drops support for a Python minor
version.

There are no more renames/URL changes planned, and we don't expect that a need
would arise to do this again in the near future.

Thanks for understanding!

- Pradyun, on behalf of the volunteers who maintain pip.
"""

print(message, file=sys.stderr)
sys.exit(1)
