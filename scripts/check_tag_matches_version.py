#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import subprocess
import tomllib
from pathlib import Path


def resolve_tag(arg: str | None) -> str:
    if arg:
        return arg

    env_tag = os.environ.get("GITHUB_REF_NAME")
    if env_tag:
        return env_tag

    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--exact-match"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        raise RuntimeError("A Git tag is required; provide --tag or set GITHUB_REF_NAME") from None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", help="Git tag like v1.0.0")
    args = parser.parse_args()

    ref_name = resolve_tag(args.tag)
    tag_version = ref_name.removeprefix("v")
    project_version = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]

    print(f"Git tag: {ref_name}")
    print(f"pyproject version: {project_version}")

    if tag_version != project_version:
        raise SystemExit(
            f"Tag version mismatch: {ref_name} does not equal project version {project_version}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
