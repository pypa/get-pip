"""Check bootstrap failures without installing packages or accessing an index."""

import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(sys.argv.pop(1)).resolve()


class BootstrapTests(unittest.TestCase):
    def run_bootstrap(self, arguments, python_arguments=()):
        """Run from a directory that would shadow an unqualified pip invocation."""
        with tempfile.TemporaryDirectory(prefix="get-pip space '") as directory:
            root = Path(directory)
            scratch = root / "scratch"
            scratch.mkdir()
            (root / "pip.py").write_text("raise SystemExit(73)\n")
            (root / "sitecustomize.py").write_text(
                "import pathlib\n"
                "pathlib.Path(__file__).with_suffix('.loaded').touch()\n"
            )
            env = os.environ.copy()
            env.update(
                TMPDIR=str(scratch),
                TEMP=str(scratch),
                TMP=str(scratch),
                PYTHONPATH=str(root),
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
            self.assertEqual(list(scratch.iterdir()), [])
            if python_arguments:
                self.assertFalse((root / "sitecustomize.loaded").exists())
            return result

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
        with patch.object(subprocess, "call", side_effect=KeyboardInterrupt):
            with self.assertRaises(SystemExit) as error:
                bootstrap("unused")
        self.assertEqual(error.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
