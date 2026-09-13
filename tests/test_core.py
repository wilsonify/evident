"""Tests for evident.core – the fundamental compare/improve_and_verify operations."""

import pytest

from evident.core import compare, improve_and_verify
from evident.models import Decision, Diagnosis, Evaluation

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Evaluators now take only the artifact; evidence is captured via closure.
def _score_evaluator(artifact: dict) -> Evaluation:
    score = artifact.get("score", 0.0)
    return Evaluation(overall=score, passed=score >= 0.5)


def _honest_improver(artifact: dict, diagnosis: Diagnosis) -> dict:
    """Returns a genuinely improved artifact."""
    return {**artifact, "score": artifact.get("score", 0.0) + 0.2}


def _lying_improver(artifact: dict, diagnosis: Diagnosis) -> dict:
    """Claims to improve but returns something worse."""
    return {**artifact, "score": artifact.get("score", 1.0) - 0.3}


def _strictly_better(before: Evaluation, after: Evaluation) -> Decision:
    accepted = after.overall > before.overall
    return Decision(
        accepted=accepted,
        reason="better" if accepted else "not better",
        before=before,
        after=after,
    )


# ---------------------------------------------------------------------------
# compare
# ---------------------------------------------------------------------------


def test_compare_accepts_improvement():
    before = Evaluation(overall=0.5)
    after = Evaluation(overall=0.8)
    decision = compare(before, after, _strictly_better)
    assert decision.accepted is True


def test_compare_rejects_regression():
    before = Evaluation(overall=0.8)
    after = Evaluation(overall=0.5)
    decision = compare(before, after, _strictly_better)
    assert decision.accepted is False


def test_compare_rejects_unchanged():
    before = Evaluation(overall=0.7)
    after = Evaluation(overall=0.7)
    decision = compare(before, after, _strictly_better)
    assert decision.accepted is False


# ---------------------------------------------------------------------------
# improve_and_verify – honest improver
# ---------------------------------------------------------------------------


def test_honest_improver_is_accepted():
    artifact = {"score": 0.5}
    result, decision = improve_and_verify(
        artifact, _score_evaluator, _honest_improver, _strictly_better
    )
    assert decision.accepted is True
    assert result["score"] == pytest.approx(0.7)


def test_honest_improver_decision_records_improvement():
    artifact = {"score": 0.5}
    _, decision = improve_and_verify(
        artifact, _score_evaluator, _honest_improver, _strictly_better
    )
    assert decision.before.overall == pytest.approx(0.5)
    assert decision.after.overall == pytest.approx(0.7)
    assert decision.improvement == pytest.approx(0.2)


def test_provenance_opt_in():
    artifact = {"score": 0.5}
    result = improve_and_verify(
        artifact, _score_evaluator, _honest_improver, _strictly_better, provenance=True
    )
    assert len(result) == 3
    _, decision, prov = result
    assert decision.accepted is True
    assert prov.before.overall == pytest.approx(0.5)
    assert prov.after.overall == pytest.approx(0.7)


def test_provenance_not_returned_by_default():
    result = improve_and_verify(
        {"score": 0.5}, _score_evaluator, _honest_improver, _strictly_better
    )
    assert len(result) == 2


# ---------------------------------------------------------------------------
# KEY INVARIANT: improver lies → framework rejects
# ---------------------------------------------------------------------------


def test_lying_improver_is_rejected():
    """The improver claims it did something useful, but independent evaluation
    shows the candidate is WORSE.  The framework must reject it."""
    artifact = {"score": 0.8}
    result, decision = improve_and_verify(
        artifact, _score_evaluator, _lying_improver, _strictly_better
    )
    assert decision.accepted is False, "Framework must not trust the improver's claim"
    # Original artifact is returned unchanged
    assert result is artifact


def test_rejected_candidate_returns_original():
    artifact = {"score": 0.9}
    result, decision = improve_and_verify(
        artifact, _score_evaluator, _lying_improver, _strictly_better
    )
    assert result is artifact
    assert result["score"] == 0.9


def test_worse_candidate_decision_records_regression():
    artifact = {"score": 0.8}
    _, decision = improve_and_verify(
        artifact, _score_evaluator, _lying_improver, _strictly_better
    )
    assert decision.after.overall < decision.before.overall


# ---------------------------------------------------------------------------
# Evaluator captures evidence via closure
# ---------------------------------------------------------------------------


def test_evaluator_closure_captures_evidence():
    """Demonstrate the idiomatic closure pattern: evaluator owns its evidence."""
    reference = "hello world"

    def evaluate(artifact: dict) -> Evaluation:
        text = artifact.get("text", "")
        score = 1.0 if text == reference else 0.0
        return Evaluation(overall=score, passed=score >= 0.9)

    def improve(artifact: dict, diagnosis: Diagnosis) -> dict:
        return {"text": reference}  # trivial "fix"

    artifact = {"text": "wrong text"}
    result, decision = improve_and_verify(artifact, evaluate, improve, _strictly_better)
    assert decision.accepted is True
    assert result["text"] == reference


# ---------------------------------------------------------------------------
# Failed evidence (evaluator raises)
# ---------------------------------------------------------------------------


def test_evaluator_exception_propagates():
    def _bad_evaluator(artifact):
        raise RuntimeError("evidence unavailable")

    with pytest.raises(RuntimeError, match="evidence unavailable"):
        improve_and_verify(
            {}, _bad_evaluator, _honest_improver, _strictly_better
        )


# ---------------------------------------------------------------------------
# Unchanged artifact
# ---------------------------------------------------------------------------


def test_unchanged_artifact_is_rejected():
    """If the improver returns the same object, the score is unchanged and it is rejected."""

    def _noop(artifact, diagnosis):
        return artifact

    artifact = {"score": 0.6}
    result, decision = improve_and_verify(
        artifact, _score_evaluator, _noop, _strictly_better
    )
    assert decision.accepted is False
    assert result is artifact


# ---------------------------------------------------------------------------
# Pass/fail evaluation
# ---------------------------------------------------------------------------


def test_pass_fail_evaluation():
    def _binary_evaluator(artifact: dict) -> Evaluation:
        score = 1.0 if artifact.get("valid") else 0.0
        return Evaluation(overall=score, passed=bool(artifact.get("valid")))

    def _fixer(artifact: dict, diagnosis: Diagnosis) -> dict:
        return {**artifact, "valid": True}

    def _must_pass(before: Evaluation, after: Evaluation) -> Decision:
        return Decision(
            accepted=after.passed,
            reason="passes" if after.passed else "fails",
            before=before,
            after=after,
        )

    artifact = {"valid": False}
    result, decision = improve_and_verify(
        artifact, _binary_evaluator, _fixer, _must_pass
    )
    assert decision.accepted is True
    assert result["valid"] is True


# ---------------------------------------------------------------------------
# Multi-metric policy (plain Python function, no DSL)
# ---------------------------------------------------------------------------


def test_multi_metric_policy():
    """Demonstrate that a plain Python policy can inspect individual metrics."""

    def _multi_eval(artifact: dict) -> Evaluation:
        a = artifact.get("a", 0.0)
        b = artifact.get("b", 0.0)
        return Evaluation(overall=(a + b) / 2, metrics={"a": a, "b": b})

    def _require_both_improve(before: Evaluation, after: Evaluation) -> Decision:
        """Accept only when ALL metrics improve."""
        both = all(
            after.metrics.get(k, 0) > before.metrics.get(k, 0)
            for k in before.metrics
        )
        reason = "both metrics improved" if both else "not all improved"
        return Decision(accepted=both, reason=reason, before=before, after=after)

    def _partial_improver(artifact: dict, _diagnosis: Diagnosis) -> dict:
        return {**artifact, "a": artifact.get("a", 0.0) + 0.5}  # only 'a' improves

    # partial improvement is rejected by the strict policy
    result, decision = improve_and_verify(
        {"a": 0.0, "b": 0.0}, _multi_eval, _partial_improver, _require_both_improve
    )
    assert decision.accepted is False
