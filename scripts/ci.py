#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys


def run(cmd: list[str]) -> None:
    print(f"+ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main() -> int:
    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    run([sys.executable, "-m", "pip", "install", "-e", ".[dev]"])
    run([sys.executable, "-m", "ruff", "check", "src", "tests"])
    run([sys.executable, "-m", "pytest", "-q"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
