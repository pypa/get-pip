# get-pip.py

`get-pip.py` is a bootstrapping script that enables users to install pip,
setuptools, and wheel in Python environments that don't already have them. You
should not directly reference the files located in this repository and instead
use the versions located at <https://bootstrap.pypa.io/>.

## Usage

```console
$ curl -sSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py
$ python get-pip.py
```

Upon execution, `get-pip.py` will install `pip`, `setuptools` and `wheel` in
the current Python environment.

It is possible to provide additional arguments to the underlying script. These
are passed through to the underlying `pip install` command, and can thus be
used to constraint the versions of the packages, or to pass other pip options
such as `--no-index`.

```console
$ python get-pip.py "pip < 21.0" "setuptools < 50.0" "wheel < 1.0"
$ python get-pip.py --no-index --find-links=/local/copies
```

### get-pip.py options

This script also has it's own options, which control which packages it will
install.

- `--no-setuptools`: do not attempt to install `setuptools`.
- `--no-wheel`: do not attempt to install `wheel`.

## Development

You need to have a [`nox`](https://nox.readthedocs.io/) available on the CLI.

### How it works

`get-pip.py` bundles a copy of pip with a tiny amount of glue code. This glue
code comes from the `templates/` directory.

### Updating after a pip release

If you just made a pip release, run `nox -s update-for-release -- <version>`.
This session will handle all the script updates (by running `generate`), commit
the changes and tag the commit.

IMPORTANT: Check that the correct files got modified before pushing. The session
will pause to let you do this.

### Generating the scripts

Run `nox -s generate`.

## Discussion

If you run into bugs, you can file them in our [issue tracker].

You can also join `#pypa` or `#pypa-dev` on Freenode to ask questions or
get involved.

[issue tracker]: https://github.com/pypa/get-pip/issues

## Code of Conduct

Everyone interacting in the get-pip project's codebases, issue trackers, chat
rooms, and mailing lists is expected to follow the [PSF Code of Conduct].

[PSF Code of Conduct]: https://github.com/pypa/.github/blob/main/CODE_OF_CONDUCT.md
