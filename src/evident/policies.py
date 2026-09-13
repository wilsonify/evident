"""Bundled acceptance policies.

A policy is a plain function: (before: Evaluation, after: Evaluation) -> Decision.
Applications can write their own.
"""

from __future__ import annotations

from collections.abc import Callable

from evident.models import Decision, Evaluation

Policy = Callable[["Evaluation", "Evaluation"], "Decision"]


def strictly_better(before: Evaluation, after: Evaluation) -> Decision:
    """Accept only when the overall score strictly improves."""
    if after.overall > before.overall:
        return Decision(
            accepted=True,
            reason=f"score improved from {before.overall:.4f} to {after.overall:.4f}",
            before=before,
            after=after,
        )
    return Decision(
        accepted=False,
        reason=f"score did not improve ({before.overall:.4f} -> {after.overall:.4f})",
        before=before,
        after=after,
    )


def must_pass(before: Evaluation, after: Evaluation) -> Decision:
    """Accept only when the candidate passes all assertions."""
    if after.passed:
        return Decision(
            accepted=True,
            reason="candidate passed all assertions",
            before=before,
            after=after,
        )
    return Decision(
        accepted=False,
        reason="candidate failed one or more assertions",
        before=before,
        after=after,
    )


def threshold(minimum: float) -> Policy:
    """Return a policy that accepts when the score meets a minimum threshold."""

    def _policy(before: Evaluation, after: Evaluation) -> Decision:
        if after.overall >= minimum:
            return Decision(
                accepted=True,
                reason=f"score {after.overall:.4f} meets threshold {minimum:.4f}",
                before=before,
                after=after,
            )
        return Decision(
            accepted=False,
            reason=f"score {after.overall:.4f} below threshold {minimum:.4f}",
            before=before,
            after=after,
        )

    return _policy
