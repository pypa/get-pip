import base64
import hashlib
import json
import os
import os.path

import urllib.request

import invoke
import packaging.specifiers
import packaging.version


PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def _path(pyversion=None):
    parts = [PROJECT_ROOT, pyversion, "get-pip.py"]
    return os.path.join(*filter(None, parts))


@invoke.task
def installer(ctx,
              version=None, installer_path=_path(),
              template_path=os.path.join(PROJECT_ROOT, "template.py")):

    print("[generate.installer] Generating installer {} (using {})".format(
        os.path.relpath(installer_path, PROJECT_ROOT),
        "pip" + version if version is not None else "latest"
    ))

    # Load our wrapper template
    with open(template_path, "r", encoding="utf8") as fp:
        WRAPPER_TEMPLATE = fp.read()

    # Get all of the versions on PyPI
    resp = urllib.request.urlopen("https://pypi.python.org/pypi/pip/json")
    data = json.loads(resp.read().decode("utf8"))
    versions = sorted(data["releases"].keys(), key=packaging.version.parse)

    # Filter our list of versions based on the given specifier
    s = packaging.specifiers.SpecifierSet("" if version is None else version)
    versions = list(s.filter(versions))

    # Select the latest version that matches our specifier is
    latest = versions[-1]

    # Select the wheel file (we assume there will be only one per release)
    file_urls = [
        (x["url"], x["md5_digest"])
        for x in data["releases"][latest]
        if x["url"].endswith(".whl")
    ]
    assert len(file_urls) == 1
    url, expected_hash = file_urls[0]

    # Fetch the  file itself.
    data = urllib.request.urlopen(url).read()
    assert hashlib.md5(data).hexdigest() == expected_hash

    # Write out the wrapper script that will take the place of the zip script
    # The reason we need to do this instead of just directly executing the
    # zip script is that while Python will happily execute a zip script if
    # passed it on the file system, it will not however allow this to work if
    # passed it via stdin. This means that this wrapper script is required to
    # make ``curl https://...../get-pip.py | python`` continue to work.
    print(
        "[generate.installer] Write the wrapper script with the bundled zip "
        "file"
    )

    zipdata = base64.b85encode(data).decode("utf8")
    chunked = []

    for i in range(0, len(zipdata), 79):
        chunked.append(zipdata[i:i + 79])

    os.makedirs(os.path.dirname(installer_path), exist_ok=True)
    with open(installer_path, "w") as fp:
        fp.write(
            WRAPPER_TEMPLATE.format(
                version="" if version is None else version,
                latest=latest,
                zipfile="\n".join(chunked),
            ),
        )

    # Ensure the permissions on the newly created file
    oldmode = os.stat(installer_path).st_mode & 0o7777
    newmode = (oldmode | 0o555) & 0o7777
    os.chmod(installer_path, newmode)

    print("[generate.installer] Generated installer")


@invoke.task(
    default=True,
    pre=[
        invoke.call(installer),
        invoke.call(installer, version="<8", installer_path=_path("3.2")),
        invoke.call(installer, version="<10", installer_path=_path("2.6")),
    ],
)
def all(ctx):
    pass
