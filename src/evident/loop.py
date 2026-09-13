"""EvidenceLoop – a convenience wrapper around the core improve_and_verify cycle."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from evident.core import Evaluator, Improver, Policy, evaluate
from evident.models import Decision, Diagnosis, Evaluation, Provenance


@dataclass
class EvidenceLoop:
    """Run iterative improve-and-verify cycles until the policy is satisfied
    or the maximum number of iterations is reached.

    Parameters
    ----------
    artifact:
        The initial artifact to improve.
    evidence:
        The evidence used for evaluation.
    evaluator:
        A function ``(artifact, evidence) -> Evaluation``.
    improver:
        A function ``(artifact, diagnosis) -> candidate``.
    policy:
        A function ``(before, after) -> Decision``.
    diagnoser:
        Optional function ``(evaluation) -> Diagnosis``.
        If omitted, a bare Diagnosis is passed to the improver.
    max_iterations:
        Maximum number of improve/verify cycles (default 10).
    artifact_id, evidence_id, evaluator_id, intervention_id:
        Human-readable identifiers recorded in provenance.
    """

    artifact: Any
    evidence: Any
    evaluator: Evaluator
    improver: Improver
    policy: Policy
    diagnoser: Callable[[Evaluation], Diagnosis] | None = None
    max_iterations: int = 10
    artifact_id: str = "artifact"
    evidence_id: str = "evidence"
    evaluator_id: str = "evaluator"
    intervention_id: str = "improver"

    history: list[Provenance] = field(default_factory=list, init=False)

    def run(self) -> tuple[Any, list[Provenance]]:
        """Run the loop.

        Returns the (possibly improved) artifact and the full provenance history.
        """
        current = self.artifact

        for _ in range(self.max_iterations):
            before = evaluate(current, self.evidence, self.evaluator)

            if self.diagnoser is not None:
                diagnosis = self.diagnoser(before)
            else:
                diagnosis = Diagnosis(summary="no diagnosis provided")

            candidate = self.improver(current, diagnosis)
            after = evaluate(candidate, self.evidence, self.evaluator)
            decision: Decision = self.policy(before, after)

            provenance = Provenance(
                artifact_id=self.artifact_id,
                evidence_id=self.evidence_id,
                evaluator_id=self.evaluator_id,
                before=before,
                after=after,
                decision=decision,
                diagnosis=diagnosis,
                intervention_id=self.intervention_id,
            )
            self.history.append(provenance)

            if decision.accepted:
                current = candidate

            # Stop if there's no improvement to chase
            if not decision.accepted:
                break

        return current, self.history
