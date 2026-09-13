"""Tests for evident.core – the fundamental evaluate/compare/improve_and_verify operations."""

import pytest

from evident.core import compare, evaluate, improve_and_verify
from evident.models import Decision, Diagnosis, Evaluation

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _score_evaluator(artifact: dict, evidence: dict) -> Evaluation:
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
# evaluate
# ---------------------------------------------------------------------------


def test_evaluate_returns_evaluation():
    result = evaluate({"score": 0.7}, {}, _score_evaluator)
    assert isinstance(result, Evaluation)
    assert result.overall == pytest.approx(0.7)


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
    result, prov = improve_and_verify(
        artifact, {}, _score_evaluator, _honest_improver, _strictly_better
    )
    assert prov.decision.accepted is True
    assert result["score"] == pytest.approx(0.7)


def test_honest_improver_provenance():
    artifact = {"score": 0.5}
    _, prov = improve_and_verify(
        artifact, {}, _score_evaluator, _honest_improver, _strictly_better
    )
    assert prov.before.overall == pytest.approx(0.5)
    assert prov.after.overall == pytest.approx(0.7)
    assert prov.decision.improvement == pytest.approx(0.2)


# ---------------------------------------------------------------------------
# KEY INVARIANT: improver lies → framework rejects
# ---------------------------------------------------------------------------


def test_lying_improver_is_rejected():
    """The improver claims it did something useful, but independent evaluation
    shows the candidate is WORSE.  The framework must reject it."""
    artifact = {"score": 0.8}
    result, prov = improve_and_verify(
        artifact, {}, _score_evaluator, _lying_improver, _strictly_better
    )
    assert prov.decision.accepted is False, "Framework must not trust the improver's claim"
    # Original artifact is returned unchanged
    assert result is artifact


def test_rejected_candidate_returns_original():
    artifact = {"score": 0.9}
    result, prov = improve_and_verify(
        artifact, {}, _score_evaluator, _lying_improver, _strictly_better
    )
    assert result is artifact
    assert result["score"] == 0.9


def test_worse_candidate_provenance_records_regression():
    artifact = {"score": 0.8}
    _, prov = improve_and_verify(
        artifact, {}, _score_evaluator, _lying_improver, _strictly_better
    )
    assert prov.after.overall < prov.before.overall


# ---------------------------------------------------------------------------
# Failed evidence (evaluator raises)
# ---------------------------------------------------------------------------


def test_evaluator_exception_propagates():
    def _bad_evaluator(artifact, evidence):
        raise RuntimeError("evidence unavailable")

    with pytest.raises(RuntimeError, match="evidence unavailable"):
        improve_and_verify(
            {}, {}, _bad_evaluator, _honest_improver, _strictly_better
        )


# ---------------------------------------------------------------------------
# Unchanged artifact
# ---------------------------------------------------------------------------


def test_unchanged_artifact_is_rejected():
    """If the improver returns the same object, the score is unchanged and it is rejected."""

    def _noop(artifact, diagnosis):
        return artifact

    artifact = {"score": 0.6}
    result, prov = improve_and_verify(
        artifact, {}, _score_evaluator, _noop, _strictly_better
    )
    assert prov.decision.accepted is False
    assert result is artifact


# ---------------------------------------------------------------------------
# Pass/fail evaluation
# ---------------------------------------------------------------------------


def test_pass_fail_evaluation():
    def _binary_evaluator(artifact, evidence):
        score = 1.0 if artifact.get("valid") else 0.0
        return Evaluation(overall=score, passed=bool(artifact.get("valid")))

    def _fixer(artifact, diagnosis):
        return {**artifact, "valid": True}

    def _must_pass(before, after):
        return Decision(
            accepted=after.passed,
            reason="passes" if after.passed else "fails",
            before=before,
            after=after,
        )

    artifact = {"valid": False}
    result, prov = improve_and_verify(
        artifact, {}, _binary_evaluator, _fixer, _must_pass
    )
    assert prov.decision.accepted is True
    assert result["valid"] is True
