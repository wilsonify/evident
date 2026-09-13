"""Tests for EvidenceLoop."""

import pytest

from evident import EvidenceLoop
from evident.models import Decision, Diagnosis, Evaluation


# Evaluators take only the artifact; evidence is captured via closure.
def _evaluator(artifact: dict) -> Evaluation:
    return Evaluation(overall=artifact.get("score", 0.0), passed=artifact.get("score", 0.0) >= 0.9)


def _improver(artifact: dict, diagnosis: Diagnosis) -> dict:
    return {**artifact, "score": min(1.0, artifact.get("score", 0.0) + 0.2)}


def _lying_improver(artifact: dict, diagnosis: Diagnosis) -> dict:
    return {**artifact, "score": artifact.get("score", 1.0) - 0.1}


def _strictly_better(before: Evaluation, after: Evaluation) -> Decision:
    accepted = after.overall > before.overall
    return Decision(accepted=accepted, reason="", before=before, after=after)


def _must_pass(before: Evaluation, after: Evaluation) -> Decision:
    return Decision(accepted=after.passed, reason="", before=before, after=after)


# ---------------------------------------------------------------------------
# Basic loop tests
# ---------------------------------------------------------------------------


def test_loop_accepts_improvement():
    loop = EvidenceLoop(
        artifact={"score": 0.5},
        evaluator=_evaluator,
        improver=_improver,
        policy=_strictly_better,
        max_iterations=1,
    )
    result, history = loop.run()
    assert len(history) == 1
    assert history[0].decision.accepted is True
    assert result["score"] == pytest.approx(0.7)


def test_loop_stops_when_rejected():
    loop = EvidenceLoop(
        artifact={"score": 0.8},
        evaluator=_evaluator,
        improver=_lying_improver,
        policy=_strictly_better,
        max_iterations=5,
    )
    result, history = loop.run()
    # Should stop after first rejection
    assert len(history) == 1
    assert history[0].decision.accepted is False
    assert result["score"] == pytest.approx(0.8)  # original returned


def test_loop_multiple_iterations():
    loop = EvidenceLoop(
        artifact={"score": 0.1},
        evaluator=_evaluator,
        improver=_improver,
        policy=_strictly_better,
        max_iterations=5,
    )
    result, history = loop.run()
    # Each accepted iteration adds 0.2 (capped at 1.0); loop stops when rejected.
    # With strictly_better and max_iterations=5, we get at most 5 entries.
    assert len(history) <= 5
    assert result["score"] >= 0.5


def test_loop_history_provenance():
    loop = EvidenceLoop(
        artifact={"score": 0.5},
        evaluator=_evaluator,
        improver=_improver,
        policy=_strictly_better,
        max_iterations=1,
        artifact_id="my-artifact",
        evaluator_id="my-evaluator",
    )
    _, history = loop.run()
    p = history[0]
    assert p.artifact_id == "my-artifact"
    assert p.evaluator_id == "my-evaluator"


# ---------------------------------------------------------------------------
# Regression detection
# ---------------------------------------------------------------------------


def test_regression_detected_and_rejected():
    """Improver introduces regression; loop detects and rejects."""
    loop = EvidenceLoop(
        artifact={"score": 0.9},
        evaluator=_evaluator,
        improver=_lying_improver,
        policy=_strictly_better,
    )
    result, history = loop.run()
    assert history[0].decision.accepted is False
    assert result["score"] == pytest.approx(0.9)


# ---------------------------------------------------------------------------
# Diagnoser integration
# ---------------------------------------------------------------------------


def test_diagnoser_is_called():
    calls = []

    def _diagnoser(evaluation: Evaluation) -> Diagnosis:
        calls.append(evaluation.overall)
        return Diagnosis(summary="diagnosed", evaluation=evaluation)

    loop = EvidenceLoop(
        artifact={"score": 0.5},
        evaluator=_evaluator,
        improver=_improver,
        policy=_strictly_better,
        diagnoser=_diagnoser,
        max_iterations=1,
    )
    loop.run()
    assert len(calls) == 1
    assert calls[0] == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Partially improved candidate
# ---------------------------------------------------------------------------


def test_partially_improved_candidate():
    """Improver gets some metrics better but overall still below threshold."""

    def _multi_eval(artifact: dict) -> Evaluation:
        a = artifact.get("a", 0.0)
        b = artifact.get("b", 0.0)
        return Evaluation(overall=(a + b) / 2, metrics={"a": a, "b": b})

    def _partial_improver(artifact: dict, diagnosis: Diagnosis) -> dict:
        return {**artifact, "a": artifact.get("a", 0.0) + 0.5}  # only improves 'a'

    def _threshold_policy(before: Evaluation, after: Evaluation) -> Decision:
        accepted = after.overall > before.overall
        return Decision(accepted=accepted, reason="", before=before, after=after)

    artifact = {"a": 0.0, "b": 0.0}
    loop = EvidenceLoop(
        artifact=artifact,
        evaluator=_multi_eval,
        improver=_partial_improver,
        policy=_threshold_policy,
        max_iterations=1,
    )
    result, history = loop.run()
    # overall improves from 0.0 to 0.25, so accepted
    assert history[0].decision.accepted is True
    assert history[0].after.metrics["a"] == pytest.approx(0.5)
    assert history[0].after.metrics["b"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Failed intervention (improver raises)
# ---------------------------------------------------------------------------


def test_failed_intervention_propagates():
    def _bad_improver(artifact, diagnosis):
        raise ValueError("intervention failed")

    loop = EvidenceLoop(
        artifact={"score": 0.5},
        evaluator=_evaluator,
        improver=_bad_improver,
        policy=_strictly_better,
    )
    with pytest.raises(ValueError, match="intervention failed"):
        loop.run()


# ---------------------------------------------------------------------------
# Closure-based evidence
# ---------------------------------------------------------------------------


def test_loop_evaluator_captures_evidence_via_closure():
    """Evaluator closes over its own evidence; loop needs no evidence param."""
    reference = "expected output"

    def evaluate(artifact: dict) -> Evaluation:
        score = 1.0 if artifact.get("text") == reference else 0.0
        return Evaluation(overall=score, passed=score >= 0.9)

    def improve(artifact: dict, _diagnosis: Diagnosis) -> dict:
        return {"text": reference}

    loop = EvidenceLoop(
        artifact={"text": "wrong"},
        evaluator=evaluate,
        improver=improve,
        policy=_strictly_better,
        max_iterations=1,
    )
    result, history = loop.run()
    assert history[0].decision.accepted is True
    assert result["text"] == reference
