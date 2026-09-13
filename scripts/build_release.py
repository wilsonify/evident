#!/usr/bin/env python3

from __future__ import annotations

import glob
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print(f"+ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main() -> int:
    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "build", "twine"])
    run([sys.executable, "-m", "build"])

    dists = sorted(glob.glob("dist/*"))
    if not dists:
        raise SystemExit("No distribution artifacts were created in dist/")

    run([sys.executable, "-m", "twine", "check", *dists])

    wheels = sorted(Path("dist").glob("*.whl"))
    if not wheels:
        raise SystemExit("No wheel found in dist/")

    wheel = wheels[0]
    run([sys.executable, "-m", "pip", "install", "--force-reinstall", str(wheel)])
    run([sys.executable, "-c", "import evident; print(evident.__file__)"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
