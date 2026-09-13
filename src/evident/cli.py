"""CLI entry point for the `evidence` command."""

from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

# ---------------------------------------------------------------------------
# Project template
# ---------------------------------------------------------------------------

_PYPROJECT = """\
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{name}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["evident"]

[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.4"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
src = ["src"]
line-length = 100
"""

_ARTIFACT = '''\
"""Artifact definition for {name}.

Replace this with your actual artifact structure.
"""

from dataclasses import dataclass


@dataclass
class Artifact:
    """The thing you want to evaluate and improve."""
    content: str
'''

_EVIDENCE = '''\
"""Evidence definition for {name}.

Replace this with your actual evidence structure.
"""

from dataclasses import dataclass


@dataclass
class Evidence:
    """Ground truth or external reference used for evaluation."""
    reference: str
'''

_EVALUATE = '''\
"""Evaluation logic for {name}.

The evaluator must be independent of the artifact and improver.
"""

from evident import Evaluation
from .artifact import Artifact
from .evidence import Evidence


def evaluate(artifact: Artifact, evidence: Evidence) -> Evaluation:
    """Return an Evaluation that measures how well artifact agrees with evidence."""
    # TODO: implement domain-specific scoring
    score = 1.0 if artifact.content == evidence.reference else 0.0
    return Evaluation(overall=score, passed=score >= 0.9)
'''

_IMPROVE = '''\
"""Improvement logic for {name}.

The improver proposes a candidate; the framework decides whether to accept it.
"""

from evident import Diagnosis
from .artifact import Artifact


def improve(artifact: Artifact, diagnosis: Diagnosis) -> Artifact:
    """Return a candidate artifact that addresses the diagnosis."""
    # TODO: implement domain-specific improvement
    return artifact
'''

_POLICY = '''\
"""Acceptance policy for {name}.

A policy is a plain function (before, after) -> Decision.
"""

from evident.policies import strictly_better as policy  # noqa: F401

# You can replace `policy` with your own function:
#
#   from evident import Decision, Evaluation
#
#   def policy(before: Evaluation, after: Evaluation) -> Decision:
#       ...
'''

_README = """\
# {name}

An evidence-driven application built with [evident](https://github.com/wilsonify/evident).

## Pattern

```
Observe → Evaluate → Diagnose → Intervene → Verify → Keep or Reject
```

## Quick start

```python
from evident import EvidenceLoop
from {pkg}.artifact import Artifact
from {pkg}.evidence import Evidence
from {pkg}.evaluate import evaluate
from {pkg}.improve import improve
from {pkg}.policy import policy

loop = EvidenceLoop(
    artifact=Artifact(content="..."),
    evidence=Evidence(reference="..."),
    evaluator=evaluate,
    improver=improve,
    policy=policy,
)
result, history = loop.run()
```

## Layout

```
src/{pkg}/
    artifact.py   – what you're evaluating
    evidence.py   – the ground truth
    evaluate.py   – independent scoring
    improve.py    – proposes a candidate
    policy.py     – accepts or rejects the candidate
tests/
    test_evaluate.py
```
"""

_TEST = '''\
"""Tests for {name}."""

from evident import EvidenceLoop
from {pkg}.artifact import Artifact
from {pkg}.evidence import Evidence
from {pkg}.evaluate import evaluate
from {pkg}.improve import improve
from {pkg}.policy import policy


def test_perfect_artifact_is_accepted():
    """Artifact identical to evidence should score 1.0 and be accepted."""
    artifact = Artifact(content="hello")
    evidence = Evidence(reference="hello")
    loop = EvidenceLoop(
        artifact=artifact,
        evidence=evidence,
        evaluator=evaluate,
        improver=improve,
        policy=policy,
    )
    result, history = loop.run()
    assert history[0].decision is not None
'''


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_init(args: argparse.Namespace) -> int:
    name: str = args.name
    pkg = name.replace("-", "_")
    root = Path(name)

    if root.exists():
        print(f"error: directory '{name}' already exists", file=sys.stderr)
        return 1

    src_pkg = root / "src" / pkg
    tests = root / "tests"
    src_pkg.mkdir(parents=True)
    tests.mkdir()

    ctx = {"name": name, "pkg": pkg}

    (root / "pyproject.toml").write_text(_PYPROJECT.format(**ctx))
    (root / "README.md").write_text(_README.format(**ctx))
    (src_pkg / "__init__.py").write_text("")
    (src_pkg / "artifact.py").write_text(_ARTIFACT.format(**ctx))
    (src_pkg / "evidence.py").write_text(_EVIDENCE.format(**ctx))
    (src_pkg / "evaluate.py").write_text(_EVALUATE.format(**ctx))
    (src_pkg / "improve.py").write_text(_IMPROVE.format(**ctx))
    (src_pkg / "policy.py").write_text(_POLICY.format(**ctx))
    (tests / "__init__.py").write_text("")
    (tests / f"test_{pkg}.py").write_text(_TEST.format(**ctx))

    print(f"Created project '{name}'")
    print(textwrap.dedent(f"""
        Layout:
          {name}/
            pyproject.toml
            README.md
            src/{pkg}/
              artifact.py   ← define your artifact
              evidence.py   ← define your evidence
              evaluate.py   ← independent scoring (edit this first)
              improve.py    ← proposes a candidate
              policy.py     ← accepts or rejects
            tests/
              test_{pkg}.py

        Next steps:
          cd {name}
          pip install -e ".[dev]"
          pytest
    """).strip())
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="evidence",
        description="evident – toolkit for evidence-driven applications",
    )
    sub = parser.add_subparsers(dest="command")

    init_p = sub.add_parser("init", help="Bootstrap a new evidence-driven project")
    init_p.add_argument("name", help="Project name (also used as directory name)")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        return cmd_init(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
