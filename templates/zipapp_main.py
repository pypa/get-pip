#!/usr/bin/env python
import sys

# /!\ This version compatibility check section must be Python 2 compatible. /!\
PYTHON_REQUIRES = ({major}, {minor})

if PYTHON_REQUIRES != (0, 0):
    def version_str(version):  # type: ignore
        return ".".join(str(v) for v in version)

    if sys.version_info[:2] < PYTHON_REQUIRES:
        raise SystemExit(
            "This version of pip does not support python " +
            version_str(sys.version_info[:2]) +
            " (requires >= " +
            version_str(PYTHON_REQUIRES) +
            ")."
        )
# /!\ Version check done. We can use Python 3 syntax now. /!\

import os
import runpy

lib = os.path.dirname(__file__)
sys.path.insert(0, lib)
runpy.run_module("pip", run_name="__main__")
