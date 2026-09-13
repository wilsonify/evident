"""Core data models for evident.

These are intentionally small, immutable dataclasses.
Application-specific logic lives outside this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Measurement:
    """A single named measurement with an optional unit and confidence."""

    name: str
    value: float
    unit: str = ""
    confidence: float = 1.0

    def __repr__(self) -> str:
        parts = [f"{self.name}={self.value:.4f}"]
        if self.unit:
            parts.append(self.unit)
        if self.confidence < 1.0:
            parts.append(f"(confidence={self.confidence:.2f})")
        return " ".join(parts)


@dataclass(frozen=True)
class Evaluation:
    """The result of evaluating an artifact against evidence.

    Separates measurement (what we observed), interpretation (what it means),
    and the overall scalar summary.
    """

    overall: float
    metrics: dict[str, float] = field(default_factory=dict)
    passed: bool = True
    label: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        lines = [f"Evaluation(overall={self.overall:.4f}, passed={self.passed}"]
        if self.metrics:
            metric_str = ", ".join(f"{k}={v:.4f}" for k, v in self.metrics.items())
            lines.append(f"  metrics: {metric_str}")
        if self.label:
            lines.append(f"  label: {self.label}")
        return "\n".join(lines) + ")"


@dataclass(frozen=True)
class Claim:
    """A statement about an artifact, annotated with a confidence."""

    statement: str
    confidence: float = 1.0
    source: str = ""


@dataclass(frozen=True)
class Hypothesis:
    """A candidate explanation for an observation."""

    id: str
    observation: str
    explanation: str
    confidence: float = 0.5
    supporting_claims: tuple[Claim, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Diagnosis:
    """The result of interpreting an evaluation: what might be wrong and why."""

    summary: str
    hypotheses: tuple[Hypothesis, ...] = field(default_factory=tuple)
    evaluation: Evaluation | None = None

    @property
    def top_hypothesis(self) -> Hypothesis | None:
        if not self.hypotheses:
            return None
        return max(self.hypotheses, key=lambda h: h.confidence)


@dataclass(frozen=True)
class Decision:
    """Accept or reject a candidate based on before/after evaluations."""

    accepted: bool
    reason: str
    before: Evaluation
    after: Evaluation

    @property
    def improvement(self) -> float:
        return self.after.overall - self.before.overall


@dataclass(frozen=True)
class Provenance:
    """A record of one evaluation/improvement cycle.

    Designed to be serialised to JSON for later inspection.
    """

    artifact_id: str
    evaluator_id: str
    before: Evaluation
    after: Evaluation | None = None
    decision: Decision | None = None
    diagnosis: Diagnosis | None = None
    intervention_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        def _eval(e: Evaluation | None) -> dict[str, Any] | None:
            if e is None:
                return None
            return {
                "overall": e.overall,
                "metrics": e.metrics,
                "passed": e.passed,
                "label": e.label,
            }

        return {
            "artifact_id": self.artifact_id,
            "evaluator_id": self.evaluator_id,
            "before": _eval(self.before),
            "after": _eval(self.after),
            "decision": (
                {
                    "accepted": self.decision.accepted,
                    "reason": self.decision.reason,
                    "improvement": self.decision.improvement,
                }
                if self.decision
                else None
            ),
            "intervention_id": self.intervention_id,
            "metadata": self.metadata,
        }
