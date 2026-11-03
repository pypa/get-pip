"""Check bootstrapping without accessing an index or modifying the environment."""

import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile


SCRIPT = Path(sys.argv.pop(1)).resolve()


class BootstrapTests(unittest.TestCase):
    def run_bootstrap(self, arguments, python_arguments=()):
        """Run from a directory that would shadow an unqualified pip invocation."""
        with tempfile.TemporaryDirectory(prefix="get-pip space '") as directory:
            root = Path(directory)
            scratch = root / "scratch"
            scratch.mkdir()
            pythonpath = root / "pythonpath"
            pythonpath.mkdir()
            for shadow in [
                root / "pip.py",
                root / "runpy.py",
                root / "logging.py",
                pythonpath / "pip.py",
            ]:
                shadow.write_text("raise SystemExit(73)\n")
            (pythonpath / "sitecustomize.py").write_text(
                "import pathlib\n"
                "pathlib.Path(__file__).with_suffix('.loaded').touch()\n"
            )
            env = os.environ.copy()
            env.update(
                TMPDIR=str(scratch),
                TEMP=str(scratch),
                TMP=str(scratch),
                PYTHONPATH=str(pythonpath),
                PIP_CONFIG_FILE=os.devnull,
            )
            command = [sys.executable] + list(python_arguments)
            command.extend(
                [
                    str(SCRIPT),
                    "--no-setuptools",
                    "--no-wheel",
                    "--isolated",
                    "--no-cache-dir",
                    "--disable-pip-version-check",
                    "--no-index",
                    "--target",
                    str(root / "target"),
                ]
            )
            result = subprocess.run(
                command + arguments,
                cwd=str(root),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
            )
            self.assertEqual(list(scratch.iterdir()), [], result.stderr.decode())
            if result.returncode == 0:
                self.assertTrue((root / "target" / "pip" / "__init__.py").is_file())
            if any(option in python_arguments for option in ("-I", "-E", "-S")):
                self.assertFalse((pythonpath / "sitecustomize.loaded").exists())
            return result

    def test_installation(self):
        # A minimal pip wheel exercises the Windows self-modification guard
        # without downloading packages or installing into the interpreter.
        with tempfile.TemporaryDirectory() as directory:
            wheel = Path(directory) / "pip-0-py3-none-any.whl"
            files = {
                "pip/__init__.py": '__version__ = "0"\n',
                "pip-0.dist-info/METADATA": "Metadata-Version: 2.1\nName: pip\nVersion: 0\n",
                "pip-0.dist-info/WHEEL": (
                    "Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
                ),
                "pip-0.dist-info/RECORD": "",
            }
            files["pip-0.dist-info/RECORD"] = "".join(name + ",,\n" for name in files)
            with ZipFile(str(wheel), "w") as archive:
                for name, content in files.items():
                    archive.writestr(name, content)
            for python_arguments in [(), ("-I",), ("-E",), ("-s",), ("-S",)]:
                with self.subTest(python_arguments=python_arguments):
                    result = self.run_bootstrap(
                        ["--find-links", directory], python_arguments
                    )
                    self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_resolution_failure(self):
        result = self.run_bootstrap(["pip==0"])
        self.assertEqual(result.returncode, 1, result.stderr.decode())

    def test_usage_failure(self):
        result = self.run_bootstrap(["--invalid-bootstrap-option"])
        self.assertEqual(result.returncode, 2, result.stderr.decode())

    def test_isolated_interpreter(self):
        result = self.run_bootstrap(["pip==0"], ["-I"])
        self.assertEqual(result.returncode, 1, result.stderr.decode())

    def test_ignored_python_environment(self):
        result = self.run_bootstrap(["pip==0"], ["-E"])
        self.assertEqual(result.returncode, 1, result.stderr.decode())

    def test_keyboard_interrupt(self):
        bootstrap = runpy.run_path(str(SCRIPT))["bootstrap"]
        with patch.object(sys, "argv", [str(SCRIPT)]):
            with patch.object(runpy, "run_module", side_effect=KeyboardInterrupt):
                with self.assertRaises(SystemExit) as error:
                    bootstrap()
        self.assertEqual(error.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
