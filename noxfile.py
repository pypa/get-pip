import os
from pathlib import Path

import nox


@nox.session
def generate(session):
    """Update the scripts, to the latest versions."""
    session.install("packaging", "requests", "cachecontrol[filecache]")

    session.run("python", "scripts/generate.py")
