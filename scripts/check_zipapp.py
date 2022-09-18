import subprocess
import sys

# This code needs to support all versions of Python we test against
proc = subprocess.Popen(
    [sys.executable] + sys.argv[1:],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
proc.wait()

out = proc.stdout.read()
err = proc.stderr.read()

if proc.returncode == 0:
    print(out)
elif b"does not support python" in err:
    print(err)
else:
    print(err)
    raise SystemExit("Failed")
