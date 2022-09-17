import subprocess
import sys

proc = subprocess.run(
    [sys.executable] + sys.argv[1:],
    capture_output=True,
)

if proc.returncode != 0:
    assert b"does not support python" in proc.stderr
