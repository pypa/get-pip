import os
import textwrap
from pathlib import Path

import nox

nox.options.sessions = ["check", "generate"]


@nox.session
def generate(session):
    """Update the scripts, to the latest versions."""
    session.install("packaging", "requests", "cachecontrol[filecache]")

    session.run("python", "scripts/generate.py")


@nox.session(name="update-for-release")
def update_for_release(session):
    """Automation to run after a pip release."""
    allowed_upstreams = [
        "git@github.com:pypa/get-pip.git",
        "https://github.com/pypa/get-pip.git",
    ]

    if len(session.posargs) != 1:
        session.error("Usage: nox -s update-for-release -- <released-pip-version>")

    release_version, = session.posargs

    session.install("release-helper")
    session.run("release-helper", "version-check-validity", release_version)
    session.run("release-helper", "git-check-tag", release_version, "--does-not-exist")
    session.run("release-helper", "git-check-remote", "upstream", *allowed_upstreams)
    session.run("release-helper", "git-check-branch", "master")
    session.run("release-helper", "git-check-clean")

    # Generate the scripts.
    generate(session)

    # Make the commit and present it to the user.
    session.run("git", "add", ".", external=True)
    session.run(
        "git", "commit", "-m", f"Update to {release_version}", external=True
    )
    session.run("git", "show", "HEAD", "--stat")

    input(textwrap.dedent(
        """\
        **********************************************
        * IMPORTANT: Check which files got modified. *
        **********************************************

        Press enter to continue. This script will generate a signed tag for this
        commit and push it -- which will publish these changes.
        """
    ))

    session.run(
        # fmt: off
        "git", "tag", release_version, "-m", f"Release {release_version}",
        "--annotate", "--sign",
        external=True,
        # fmt: on
    )
    session.run("git", "push", "upstream", "master", release_version, external=True)
