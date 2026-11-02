#!/usr/bin/env python
#
# Hi There!
#
# You may be wondering what this giant blob of binary data here is, you might
# even be worried that we're up to something nefarious (good for you for being
# paranoid!). This is a base85 encoding of a zip file, this zip file contains
# an entire copy of pip (version {installed_version}).
#
# Pip is a thing that installs packages, pip itself is a package that someone
# might want to install, especially if they're looking to run this get-pip.py
# script. Pip has a lot of code to deal with the security of installing
# packages, various edge cases on various platforms, and other such sort of
# "tribal knowledge" that has been encoded in its code base. Because of this
# we basically include an entire copy of pip inside this blob. We do this
# because the alternatives are attempt to implement a "minipip" that probably
# doesn't do things correctly and has weird edge cases, or compress pip itself
# down into a single file.
#
# If you're wondering how this is created, it is generated using
# `scripts/generate.py` in https://github.com/pypa/get-pip.

import sys

this_python = sys.version_info[:2]
min_version = {minimum_supported_version}
if this_python < min_version:
    message_parts = [
        "This script does not work on Python {{}}.{{}}.".format(*this_python),
        "The minimum supported Python version is {{}}.{{}}.".format(*min_version),
        "Please use https://bootstrap.pypa.io/pip/{{}}.{{}}/get-pip.py instead.".format(*this_python),
    ]
    print("ERROR: " + " ".join(message_parts))
    sys.exit(1)


import argparse
import importlib.util
import io
import os.path
import shutil
import subprocess
import tempfile
from base64 import b85decode
from zipfile import ZipFile


def include_setuptools(args):
    """
    Install setuptools only if absent, not excluded and when using Python <3.12.
    """
    cli = not args.no_setuptools
    env = not os.environ.get("PIP_NO_SETUPTOOLS")
    absent = not importlib.util.find_spec("setuptools")
    python_lt_3_12 = this_python < (3, 12)
    return cli and env and absent and python_lt_3_12


def include_wheel(args):
    """
    Install wheel only if absent, not excluded and when using Python <3.12.
    """
    cli = not args.no_wheel
    env = not os.environ.get("PIP_NO_WHEEL")
    absent = not importlib.util.find_spec("wheel")
    python_lt_3_12 = this_python < (3, 12)
    return cli and env and absent and python_lt_3_12


def determine_pip_install_arguments():
    pre_parser = argparse.ArgumentParser()
    pre_parser.add_argument("--no-setuptools", action="store_true")
    pre_parser.add_argument("--no-wheel", action="store_true")
    pre, args = pre_parser.parse_known_args()

    args.append("pip{pip_version}")

    if include_setuptools(pre):
        args.append("setuptools{setuptools_version}")

    if include_wheel(pre):
        args.append("wheel{wheel_version}")

    return ["install", "--upgrade", "--force-reinstall"] + args


def bootstrap(tmpdir):
    command = [sys.executable]
    # Preserve the caller's import isolation in the child interpreter.
    for option, enabled in (
        ("-I", sys.flags.isolated),
        ("-E", sys.flags.ignore_environment),
        ("-s", sys.flags.no_user_site),
        ("-S", sys.flags.no_site),
    ):
        if enabled:
            command.append(option)

    # Running the package directory selects the bundled pip without changing cwd or PYTHONPATH.
    command.append(os.path.join(tmpdir, "pip"))
    try:
        returncode = subprocess.call(command + determine_pip_install_arguments())
    except KeyboardInterrupt:
        returncode = 1

    sys.exit(returncode)


def main():
    tmpdir = None
    try:
        # Create a temporary working directory
        tmpdir = tempfile.mkdtemp()

        # Extract certificates along with pip so their default paths are usable.
        with ZipFile(io.BytesIO(b85decode(DATA.replace(b"\n", b"")))) as pip_zip:
            pip_zip.extractall(tmpdir)

        # Run the bootstrap
        bootstrap(tmpdir=tmpdir)
    finally:
        # Clean up our temporary working directory
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)


DATA = b"""
{zipfile}
"""


if __name__ == "__main__":
    main()
