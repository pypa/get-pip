import base64
import hashlib
import io
import json
import os
import os.path
import re
import zipfile

import urllib.request

import invoke
import packaging.specifiers
import packaging.version


PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def _path(pyversion=None):
    parts = [PROJECT_ROOT, pyversion, "get-pip.py"]
    return os.path.join(*filter(None, parts))


def _template(name="default.py"):
    return os.path.join(PROJECT_ROOT, "templates", name)


@invoke.task
def installer(ctx,
              pip_version=None, wheel_version=None, setuptools_version=None,
              installer_path=_path(), template_path=_template()):

    print("[generate.installer] Generating installer {} (using {})".format(
        os.path.relpath(installer_path, PROJECT_ROOT),
        "pip" + pip_version if pip_version is not None else "latest"
    ))

    # Load our wrapper template
    with open(template_path, "r", encoding="utf8") as fp:
        WRAPPER_TEMPLATE = fp.read()

    # Get all of the versions on PyPI
    resp = urllib.request.urlopen("https://pypi.python.org/pypi/pip/json")
    data = json.loads(resp.read().decode("utf8"))
    versions = sorted(data["releases"].keys(), key=packaging.version.parse)

    # Filter our list of versions based on the given specifier
    s = packaging.specifiers.SpecifierSet(
        "" if pip_version is None else pip_version)
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

    # We need to repack the downloaded wheel file to remove the .dist-info,
    # after this it will no longer be a valid wheel, but it will still work
    # perfectly fine for our use cases.
    new_data = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(data)) as existing_zip:
        with zipfile.ZipFile(new_data, mode="w") as new_zip:
            for zinfo in existing_zip.infolist():
                if re.search(r"pip-.+\.dist-info/", zinfo.filename):
                    continue
                new_zip.writestr(zinfo, existing_zip.read(zinfo))
    data = new_data.getvalue()

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
                pip_version="" if pip_version is None else pip_version,
                wheel_version="" if wheel_version is None else wheel_version,
                setuptools_version=(
                    "" if setuptools_version is None else setuptools_version),
                installed_version=latest,
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
        invoke.call(installer, installer_path=_path("2.6"),
                    template_path=_template("pre-10.py"),
                    pip_version="<10",
                    wheel_version="<0.30",
                    setuptools_version="<37"),
        invoke.call(installer, installer_path=_path("3.2"),
                    template_path=_template("pre-10.py"),
                    pip_version="<8",
                    wheel_version="<0.30",
                    setuptools_version="<30"),
        invoke.call(installer, installer_path=_path("3.3"),
                    template_path=_template("pre-18.1.py"),
                    pip_version="<18",
                    wheel_version="<0.30"),
        invoke.call(installer, installer_path=_path("3.4"),
                    template_path=_template("pre-19.3.py"),
                    pip_version="<19.2"),
    ],
)
def all(ctx):
    pass
