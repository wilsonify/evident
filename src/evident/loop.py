"""EvidenceLoop – a convenience wrapper around the core improve_and_verify cycle."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from evident.core import Evaluator, Improver, Policy
from evident.models import Decision, Diagnosis, Evaluation, Provenance


@dataclass
class EvidenceLoop:
    """Run iterative improve-and-verify cycles until the policy is satisfied
    or the maximum number of iterations is reached.

    Parameters
    ----------
    artifact:
        The initial artifact to improve.
    evaluator:
        A function ``(artifact) -> Evaluation``.
        The evaluator captures its own evidence via closure, keeping the
        loop API evidence-agnostic.
    improver:
        A function ``(artifact, diagnosis) -> candidate``.
    policy:
        A function ``(before, after) -> Decision``.
    diagnoser:
        Optional function ``(evaluation) -> Diagnosis``.
        If omitted, a bare Diagnosis is passed to the improver.
    max_iterations:
        Maximum number of improve/verify cycles (default 10).
    artifact_id, evaluator_id, intervention_id:
        Human-readable identifiers recorded in provenance.
    """

    artifact: Any
    evaluator: Evaluator
    improver: Improver
    policy: Policy
    diagnoser: Callable[[Evaluation], Diagnosis] | None = None
    max_iterations: int = 10
    artifact_id: str = "artifact"
    evaluator_id: str = "evaluator"
    intervention_id: str = "improver"

    history: list[Provenance] = field(default_factory=list, init=False)

    def run(self) -> tuple[Any, list[Provenance]]:
        """Run the loop.

        Returns the (possibly improved) artifact and the full provenance history.
        """
        self.history = []
        current = self.artifact
        cached_eval: Evaluation | None = None  # reuse accepted `after` as next `before`

        for _ in range(self.max_iterations):
            before = cached_eval if cached_eval is not None else self.evaluator(current)

            if self.diagnoser is not None:
                diagnosis = self.diagnoser(before)
            else:
                diagnosis = Diagnosis(summary="no diagnosis provided")

            candidate = self.improver(current, diagnosis)
            after = self.evaluator(candidate)
            decision: Decision = self.policy(before, after)

            provenance = Provenance(
                artifact_id=self.artifact_id,
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
                cached_eval = after  # reuse this evaluation as `before` next iteration
            else:
                break

        return current, self.history
