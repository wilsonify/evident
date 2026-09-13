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
Evaluator = Callable[[Any], Evaluation]
Improver = Callable[[Any, Diagnosis], Any]
Policy = Callable[[Evaluation, Evaluation], Decision]


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------


def compare(before: Evaluation, after: Evaluation, policy: Policy) -> Decision:
    """Compare two evaluations using an application-supplied acceptance policy.

    The policy decides what "better" means for this application.
    The framework never hard-codes an acceptance criterion.
    """
    return policy(before, after)


def improve_and_verify(
    artifact: Artifact,
    evaluator: Evaluator,
    improver: Improver,
    policy: Policy,
    diagnosis: Diagnosis | None = None,
    *,
    provenance: bool = False,
    artifact_id: str = "artifact",
    evaluator_id: str = "evaluator",
    intervention_id: str = "improver",
) -> tuple[Artifact, Decision] | tuple[Artifact, Decision, Provenance]:
    """Run one full improve-and-verify cycle.

    The evaluator is a plain callable ``artifact -> Evaluation``.
    It captures its own evidence via closure, keeping the API minimal.

    The improver is never trusted.  The framework re-evaluates the candidate
    independently and only accepts it when the policy says so.

    Parameters
    ----------
    artifact:
        The artifact to improve.
    evaluator:
        ``(artifact) -> Evaluation``.  Must be independent of the improver.
    improver:
        ``(artifact, diagnosis) -> candidate``.
    policy:
        ``(before, after) -> Decision``.
    diagnosis:
        Optional diagnosis to pass to the improver.  A bare Diagnosis is
        created when omitted.
    provenance:
        When ``True``, also return a :class:`Provenance` record as the third
        element of the result tuple.
    artifact_id, evaluator_id, intervention_id:
        Identifiers recorded in the Provenance record (used only when
        ``provenance=True``).

    Returns
    -------
    ``(accepted_artifact, decision)`` normally, or
    ``(accepted_artifact, decision, provenance)`` when ``provenance=True``.
    """
    if diagnosis is None:
        diagnosis = Diagnosis(summary="no diagnosis provided")

    before = evaluator(artifact)
    candidate = improver(artifact, diagnosis)
    after = evaluator(candidate)
    decision = compare(before, after, policy)

    accepted_artifact = candidate if decision.accepted else artifact

    if provenance:
        prov = Provenance(
            artifact_id=artifact_id,
            evaluator_id=evaluator_id,
            before=before,
            after=after,
            decision=decision,
            diagnosis=diagnosis,
            intervention_id=intervention_id,
        )
        return accepted_artifact, decision, prov

    return accepted_artifact, decision
