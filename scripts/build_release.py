#!/usr/bin/env python3

from __future__ import annotations

import glob
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd: list[str]) -> None:
    print(f"+ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def verify_install(artifact: str) -> None:
    with tempfile.TemporaryDirectory(prefix="evident-release-") as tmpdir:
        venv = Path(tmpdir) / "venv"
        run([sys.executable, "-m", "venv", str(venv)])
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

        run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
        run([str(python), "-m", "pip", "install", artifact])
        run([
            str(python),
            "-c",
            "import importlib.metadata as md; pkg = md.metadata('evidentkit'); print(pkg['Name']); print(pkg['Version']);",
        ])


def main() -> int:
    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "build", "twine"])
    run([sys.executable, "-m", "build"])

    dists = sorted(glob.glob("dist/*"))
    if not dists:
        raise SystemExit("No distribution artifacts were created in dist/")

    run([sys.executable, "-m", "twine", "check", *dists])

    wheel = sorted(Path("dist").glob("*.whl"))
    sdist = sorted(Path("dist").glob("*.tar.gz"))
    if not wheel or not sdist:
        raise SystemExit("Both wheel and sdist must be present in dist/")

    verify_install(str(wheel[0]))
    verify_install(str(sdist[0]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
