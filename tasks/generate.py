import base64
import hashlib
import json
import os
import os.path

import urllib.request

import invoke


PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


@invoke.task(default=True)
def installer(template_path=os.path.join(PROJECT_ROOT, "template.py"),
              installer_path=os.path.join(PROJECT_ROOT, "get-pip.py")):

    print("[generate.installer] Generating installer")

    # Load our wrapper template
    with open(template_path, "r", encoding="utf8") as fp:
        WRAPPER_TEMPLATE = fp.read()

    # Determine what the latest version of pip on PyPI is.
    resp = urllib.request.urlopen("https://pypi.python.org/pypi/pip/json")
    data = json.loads(resp.read().decode("utf8"))
    version = data["info"]["version"]
    file_urls = [
        (x["url"], x["md5_digest"])
        for x in data["releases"][version]
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

    with open(installer_path, "w") as fp:
        fp.write(WRAPPER_TEMPLATE.format(zipfile="\n".join(chunked)))

    # Ensure the permissions on the newly created file
    oldmode = os.stat(installer_path).st_mode & 0o7777
    newmode = (oldmode | 0o555) & 0o7777
    os.chmod(installer_path, newmode)

    print("[generate.installer] Generated installer")
