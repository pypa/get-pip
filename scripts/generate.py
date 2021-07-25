"""Update all the get-pip.py scripts."""

import itertools
import operator
import re
from base64 import b85encode
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Dict, Iterable, List, TextIO, Tuple
from zipfile import ZipFile

import requests
from cachecontrol import CacheControl
from cachecontrol.caches.file_cache import FileCache
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from rich.console import Console

SCRIPT_CONSTRAINTS = {
    "default": {
        "pip": "",
        "setuptools": "",
        "wheel": "",
    },
    "2.6": {
        "pip": "<10",
        "setuptools": "<37",
        "wheel": "<0.30",
    },
    "2.7": {
        "pip": "<21.0",
        "setuptools": "<45",
        "wheel": "",
    },
    "3.2": {
        "pip": "<8",
        "setuptools": "<30",
        "wheel": "<0.30",
    },
    "3.3": {
        "pip": "<18",
        "setuptools": "",
        "wheel": "<0.30",
    },
    "3.4": {
        "pip": "<19.2",
        "setuptools": "",
        "wheel": "",
    },
    "3.5": {
        "pip": "<21.0",
        "setuptools": "",
        "wheel": "",
    },
}

# Scripts here use the "moved" template, with the key being the file path and
# value being the path on bootstrap.pypa.io that the user should use instead.
#
# For example, the following dictionary:
#
# {
#     "2.6/get-pip.py": "pip/2.6/get-pip.py",
# }
#
# Will roughly translate to:
#
# - generate a script at `2.6/get-pip.py`
# - the generated script tells the users to change their URL to
#   https://bootstrap.pypa.io/pip/2.6/get-pip.py
#
# This is useful when restructuring this repository, like what we did in early 2021.
MOVED_SCRIPTS: Dict[str, str] = {}


def get_all_pip_versions() -> Dict[Version, Tuple[str, str]]:
    data = requests.get("https://pypi.python.org/pypi/pip/json").json()

    versions = sorted(Version(s) for s in data["releases"].keys())

    retval = {}
    for version in versions:
        wheels = [
            (file["url"], file["md5_digest"])
            for file in data["releases"][str(version)]
            if file["url"].endswith(".whl")
        ]
        if not wheels:
            continue
        assert len(wheels) == 1, (version, wheels)
        retval[version] = wheels[0]
    return retval


def determine_latest(versions: Iterable[Version], *, constraint: str):
    assert sorted(versions) == list(versions)
    return list(SpecifierSet(constraint).filter(versions))[-1]


@lru_cache
def get_ordered_templates() -> List[Tuple[Version, Path]]:
    """Get an ordered list of templates, based on the max version they support.

    This looks at the templates directory, trims the "pre-" from the files,
    and returns a sorted list of (version, template_path) tuples.
    """
    all_templates = list(Path("./templates").iterdir())

    fallback = None
    ordered_templates = []
    for template in all_templates:
        # `moved.py` isn't one of the templates to be used here.
        if template.name == "moved.py":
            continue
        if template.name == "default.py":
            fallback = template
            continue
        assert template.name.startswith("pre-")

        version_str = template.name[4:-3]  # "pre-{version}.py"
        version = Version(version_str)
        ordered_templates.append((version, template))

    # Use the epoch mechanism, to force the fallback to the end.
    assert fallback is not None
    assert fallback.name == "default.py"
    ordered_templates.append((Version("1!0"), fallback))

    # Order the (version, template) tuples, by increasing version numbers.
    return sorted(ordered_templates, key=operator.itemgetter(0))


def determine_template(version: Version):
    ordered_templates = get_ordered_templates()
    for template_version, template in ordered_templates:
        if version < template_version:
            return template
    else:
        assert template.name == "default.py"
        return template


def download_wheel(url: str, expected_md5: str) -> bytes:
    session = requests.session()
    cached_session = CacheControl(session, cache=FileCache(".web_cache"))

    response = cached_session.get(url)
    return response.content


def populated_script_constraints(original_constraints):
    """Yields the original constraints, with `minimum_supported_version` added.

    For `M.N/get-pip.py`, it would be "(M, N)".

    For the "default" get-pip.py, it would be "(M, N+1)" where M.N is the
    highest version in the rest of the mapping.

    Also, the yield order is defined as "default" and then versions in
    increasing order.
    """
    sorted_python_versions = sorted(set(original_constraints) - {"default"})
    for variant in itertools.chain(["default"], sorted_python_versions):
        if variant == "default":
            major, minor = map(int, sorted_python_versions[-1].split("."))
            minor += 1
        else:
            major, minor = map(int, variant.split("."))

        mapping = original_constraints[variant].copy()
        mapping["minimum_supported_version"] = f"({major}, {minor})"

        yield variant, mapping


def repack_wheel(data: bytes):
    """Remove the .dist-info, so that this is no longer a valid wheel."""
    new_data = BytesIO()
    with ZipFile(BytesIO(data)) as existing_zip:
        with ZipFile(new_data, mode="w") as new_zip:
            for zipinfo in existing_zip.infolist():
                if re.search(r"pip-.+\.dist-info/", zipinfo.filename):
                    continue
                new_zip.writestr(zipinfo, existing_zip.read(zipinfo))

    return new_data.getvalue()


def encode_wheel_contents(data: bytes) -> str:
    zipdata = b85encode(data).decode("utf8")

    chunked = []
    for i in range(0, len(zipdata), 79):
        chunked.append(zipdata[i : i + 79])

    return "\n".join(chunked)


def determine_destination(base: str, variant: str) -> Path:
    public = Path(base)
    if not public.exists():
        public.mkdir()

    if variant == "default":
        return public / "get-pip.py"

    retval = public / variant / "get-pip.py"
    if not retval.parent.exists():
        retval.parent.mkdir()

    return retval


def detect_newline(f: TextIO) -> str:
    newline = f.newlines
    if not newline:
        return "\n"  # Default to LF.
    if isinstance(newline, str):
        return newline
    return "\n"  # Template has mixed newlines, default to LF.


def generate_one(variant, mapping, *, console, pip_versions):
    # Determing the correct wheel to download
    pip_version = determine_latest(pip_versions.keys(), constraint=mapping["pip"])
    wheel_url, wheel_hash = pip_versions[pip_version]

    console.log(f"  Downloading [green]{Path(wheel_url).name}")
    original_wheel = download_wheel(wheel_url, wheel_hash)
    repacked_wheel = repack_wheel(original_wheel)
    encoded_wheel = encode_wheel_contents(repacked_wheel)

    # Generate the script, by rendering the template
    template = determine_template(pip_version)
    console.log(f"  Rendering [yellow]{template}")
    with template.open() as f:
        newline = detect_newline(f)
        rendered_template = f.read().format(
            zipfile=encoded_wheel,
            installed_version=pip_version,
            pip_version=mapping["pip"],
            setuptools_version=mapping["setuptools"],
            wheel_version=mapping["wheel"],
            minimum_supported_version=mapping["minimum_supported_version"],
        )
    # Write the script to the correct location
    destination = determine_destination("public", variant)
    console.log(f"  Writing [blue]{destination}")
    with destination.open("w", newline=newline) as f:
        f.write(rendered_template)


def generate_moved(destination: str, *, location: str, console: Console):
    template = Path("templates") / "moved.py"
    assert template.exists()

    with template.open() as f:
        newline = detect_newline(f)
        rendered_template = f.read().format(location=location)
    console.log(f"  Writing [blue]{destination}[reset]")
    console.log(f"    Points users to [cyan]{location}[reset]")
    with open(destination, "w", newline=newline) as f:
        f.write(rendered_template)


def main() -> None:
    console = Console()
    with console.status("Fetching pip versions..."):
        pip_versions = get_all_pip_versions()
        console.log(f"Found {len(pip_versions)} available pip versions.")
        console.log(f"Latest version: {max(pip_versions)}")

    with console.status("Generating scripts...") as status:
        for variant, mapping in populated_script_constraints(SCRIPT_CONSTRAINTS):
            status.update(f"Working on [magenta]{variant}")
            console.log(f"[magenta]{variant}")

            generate_one(variant, mapping, console=console, pip_versions=pip_versions)

    if MOVED_SCRIPTS:
        console.log("[magenta]Generating 'moved' scripts...")
        with console.status("Generating 'moved' scripts...") as status:
            for legacy, current in MOVED_SCRIPTS.items():
                status.update(f"Working on [magenta]{legacy}")
                generate_moved(legacy, console=console, location=current)


if __name__ == "__main__":
    main()
