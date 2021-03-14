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
        "This script does not work on Python {{}}.{{}}".format(*this_python),
        "The minimum supported Python version is {{}}.{{}}.".format(*min_version),
        "Please use https://bootstrap.pypa.io/pip/{{}}.{{}}/get-pip.py instead.".format(*this_python),
    ]
    print("ERROR: " + " ".join(message_parts))
    sys.exit(1)


import os.path
import pkgutil
import shutil
import tempfile
from base64 import b85decode


def determine_pip_install_arguments():
    implicit_pip = True
    implicit_setuptools = True
    implicit_wheel = True

    # Check if the user has requested us not to install setuptools
    if "--no-setuptools" in sys.argv or os.environ.get("PIP_NO_SETUPTOOLS"):
        args = [x for x in sys.argv[1:] if x != "--no-setuptools"]
        implicit_setuptools = False
    else:
        args = sys.argv[1:]

    # Check if the user has requested us not to install wheel
    if "--no-wheel" in args or os.environ.get("PIP_NO_WHEEL"):
        args = [x for x in args if x != "--no-wheel"]
        implicit_wheel = False

    # We only want to implicitly install setuptools and wheel if they don't
    # already exist on the target platform.
    if implicit_setuptools:
        try:
            import setuptools  # noqa
            implicit_setuptools = False
        except ImportError:
            pass
    if implicit_wheel:
        try:
            import wheel  # noqa
            implicit_wheel = False
        except ImportError:
            pass

    # Add any implicit installations to the end of our args
    if implicit_pip:
        args += ["pip{pip_version}"]
    if implicit_setuptools:
        args += ["setuptools{setuptools_version}"]
    if implicit_wheel:
        args += ["wheel{wheel_version}"]

    return ["install", "--upgrade", "--force-reinstall"] + args


def monkeypatch_for_cert(tmpdir):
    """Patches `pip install` to provide default certificate with the lowest priority.

    This ensures that the bundled certificates are used unless the user specifies a
    custom cert via any of pip's option passing mechanisms (config, env-var, CLI).

    A monkeypatch is the easiest way to achieve this, without messing too much with
    the rest of pip's internals.
    """
    from pip._internal.commands.install import InstallCommand

    # We want to be using the internal certificates.
    cert_path = os.path.join(tmpdir, "cacert.pem")
    with open(cert_path, "wb") as cert:
        cert.write(pkgutil.get_data("pip._vendor.certifi", "cacert.pem"))

    install_parse_args = InstallCommand.parse_args

    def cert_parse_args(self, args):
        if not self.parser.get_default_values().cert:
            # There are no user provided cert -- force use of bundled cert
            self.parser.defaults["cert"] = cert_path  # calculated above
        return install_parse_args(self, args)

    InstallCommand.parse_args = cert_parse_args


def bootstrap(tmpdir):
    monkeypatch_for_cert(tmpdir)

    # Execute the included pip and use it to install the latest pip and
    # setuptools from PyPI
    from pip._internal.cli.main import main as pip_entry_point
    args = determine_pip_install_arguments()
    sys.exit(pip_entry_point(args))


def main():
    tmpdir = None
    try:
        # Create a temporary working directory
        tmpdir = tempfile.mkdtemp()

        # Unpack the zipfile into the temporary directory
        pip_zip = os.path.join(tmpdir, "pip.zip")
        with open(pip_zip, "wb") as fp:
            fp.write(b85decode(DATA.replace(b"\n", b"")))

        # Add the zipfile to sys.path so that we can import it
        sys.path.insert(0, pip_zip)

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
