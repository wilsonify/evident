"""Core operations for evidence-driven evaluation.

These are plain functions, not class methods.
Applications compose them as needed.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from evident.models import Decision, Diagnosis, Evaluation, Provenance

# ---------------------------------------------------------------------------
# Type aliases (no runtime cost)
# ---------------------------------------------------------------------------

Artifact = Any
Evidence = Any
Evaluator = Callable[[Artifact, Evidence], Evaluation]
Improver = Callable[[Artifact, Diagnosis], Artifact]
Policy = Callable[[Evaluation, Evaluation], Decision]


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------


def evaluate(artifact: Artifact, evidence: Evidence, evaluator: Evaluator) -> Evaluation:
    """Evaluate an artifact against evidence using the provided evaluator.

    The evaluator is application-supplied and must NOT be the same component
    that produced or modified the artifact.
    """
    return evaluator(artifact, evidence)


def compare(before: Evaluation, after: Evaluation, policy: Policy) -> Decision:
    """Compare two evaluations using an application-supplied acceptance policy.

    The policy decides what "better" means for this application.
    The framework never hard-codes an acceptance criterion.
    """
    return policy(before, after)


def improve_and_verify(
    artifact: Artifact,
    evidence: Evidence,
    evaluator: Evaluator,
    improver: Improver,
    policy: Policy,
    diagnosis: Diagnosis | None = None,
    *,
    artifact_id: str = "artifact",
    evidence_id: str = "evidence",
    evaluator_id: str = "evaluator",
    intervention_id: str = "improver",
) -> tuple[Artifact, Provenance]:
    """Run one full improve-and-verify cycle.

    The improver is never trusted.  The framework re-evaluates the candidate
    independently and only accepts it when the policy says so.

    Returns the accepted artifact (original if rejected) and a Provenance record.
    """
    if diagnosis is None:
        diagnosis = Diagnosis(summary="no diagnosis provided")

    before = evaluate(artifact, evidence, evaluator)
    candidate = improver(artifact, diagnosis)
    after = evaluate(candidate, evidence, evaluator)
    decision = compare(before, after, policy)

    provenance = Provenance(
        artifact_id=artifact_id,
        evidence_id=evidence_id,
        evaluator_id=evaluator_id,
        before=before,
        after=after,
        decision=decision,
        diagnosis=diagnosis,
        intervention_id=intervention_id,
    )

    accepted_artifact = candidate if decision.accepted else artifact
    return accepted_artifact, provenance
