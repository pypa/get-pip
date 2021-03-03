#!/usr/bin/env python
from __future__ import print_function
import sys
import textwrap

message = """
Hi there!

The URL you are using to fetch this script has changed, and this one will no
longer work. Please use get-pip.py from the following URL instead:

    https://bootstrap.pypa.io/{location}

Sorry if this change causes any inconvenience for you!
"""

print(message, file=sys.stderr)
sys.exit(1)
