#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import sys
import tomllib
from pathlib import Path

from packaging import version


def resolve_tag(arg: str | None) -> str:
    if arg:
        return arg

    env_tag = os.environ.get("GITHUB_REF_NAME")
    if env_tag:
        return env_tag

    raise RuntimeError("A Git tag is required; provide --tag or set GITHUB_REF_NAME")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", help="Git tag like v1.0.0")
    args = parser.parse_args()

    ref_name = resolve_tag(args.tag)
    if not ref_name.startswith("v"):
        raise SystemExit(f"Tag must start with 'v': {ref_name!r}")

    tag_value = ref_name[1:]
    try:
        version.Version(tag_value)
    except version.InvalidVersion as exc:
        raise SystemExit(f"Invalid PEP 440 version tag: {ref_name!r}") from exc

    project_version = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    try:
        version.Version(project_version)
    except version.InvalidVersion as exc:
        raise SystemExit(f"Invalid PEP 440 project version: {project_version!r}") from exc

    print(f"Git tag: {ref_name}")
    print(f"pyproject version: {project_version}")

    if tag_value != project_version:
        raise SystemExit(
            f"Tag version mismatch: {ref_name} does not equal project version {project_version}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
