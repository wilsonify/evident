"""Example: configuration improved against a validation suite.

A config dict is evaluated against required rules.
The improver adds missing keys with default values.

Run this example:
    python examples/config_validation/run.py
"""

from __future__ import annotations

from dataclasses import dataclass, field

from evident import Diagnosis, Evaluation, EvidenceLoop
from evident.policies import must_pass


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


@dataclass
class Config:
    """An artifact: a configuration mapping."""

    data: dict[str, object] = field(default_factory=dict)


@dataclass
class ValidationSuite:
    """Evidence: rules that the config must satisfy."""

    required_keys: list[str]
    defaults: dict[str, object] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------


def evaluate(config: Config, suite: ValidationSuite) -> Evaluation:
    missing = [k for k in suite.required_keys if k not in config.data]
    present = [k for k in suite.required_keys if k in config.data]
    coverage = len(present) / max(len(suite.required_keys), 1)
    passed = len(missing) == 0
    return Evaluation(
        overall=coverage,
        metrics={"coverage": coverage},
        passed=passed,
        label="config-coverage",
        details={"missing": missing},
    )


# ---------------------------------------------------------------------------
# Improver
# ---------------------------------------------------------------------------


def improve(config: Config, diagnosis: Diagnosis) -> Config:
    """Add missing keys using defaults from the evaluation details."""
    # The improver reads diagnosis details to know what to fix.
    # A real improver might ask a human or call an LLM.
    missing: list[str] = diagnosis.evaluation.details.get("missing", []) if diagnosis.evaluation else []
    new_data = dict(config.data)
    for key in missing:
        new_data[key] = f"<default-{key}>"
    return Config(data=new_data)


def diagnoser(evaluation: Evaluation) -> Diagnosis:
    """Translate an evaluation into a diagnosis the improver can act on."""
    return Diagnosis(
        summary=f"Config missing {len(evaluation.details.get('missing', []))} required keys",
        evaluation=evaluation,
    )


# ---------------------------------------------------------------------------
# Demo run
# ---------------------------------------------------------------------------


def run() -> None:
    artifact = Config(data={"host": "localhost"})
    evidence = ValidationSuite(required_keys=["host", "port", "timeout"])

    loop = EvidenceLoop(
        artifact=artifact,
        evidence=evidence,
        evaluator=evaluate,
        improver=improve,
        policy=must_pass,
        diagnoser=diagnoser,
        artifact_id="app-config",
        evidence_id="validation-suite",
        evaluator_id="config-coverage-evaluator",
    )

    result, history = loop.run()

    print("=== Config Validation Example ===")
    for i, p in enumerate(history):
        print(f"\nIteration {i + 1}:")
        print(f"  before : {p.before.overall:.3f} (passed={p.before.passed})")
        print(f"  after  : {p.after.overall:.3f} (passed={p.after.passed})")
        print(f"  accepted: {p.decision.accepted} – {p.decision.reason}")

    print(f"\nFinal config: {result.data}")


if __name__ == "__main__":
    run()
