"""Tests for evident.models."""

from evident.models import (
    Claim,
    Decision,
    Diagnosis,
    Evaluation,
    Hypothesis,
    Measurement,
    Provenance,
)


def test_measurement_repr():
    m = Measurement(name="accuracy", value=0.95, confidence=0.8)
    assert "accuracy" in repr(m)
    assert "confidence" in repr(m)


def test_evaluation_defaults():
    e = Evaluation(overall=0.9)
    assert e.passed is True
    assert e.metrics == {}
    assert e.label == ""


def test_evaluation_multiple_metrics():
    e = Evaluation(overall=0.947, metrics={"timing": 0.981, "coverage": 0.932})
    assert e.metrics["timing"] == 0.981
    assert e.metrics["coverage"] == 0.932


def test_claim_defaults():
    c = Claim(statement="the sky is blue")
    assert c.confidence == 1.0
    assert c.source == ""


def test_hypothesis_top_confidence():
    h1 = Hypothesis(id="H1", observation="obs1", explanation="exp1", confidence=0.71)
    h2 = Hypothesis(id="H2", observation="obs2", explanation="exp2", confidence=0.45)
    d = Diagnosis(summary="test", hypotheses=(h1, h2))
    assert d.top_hypothesis is h1


def test_diagnosis_no_hypotheses():
    d = Diagnosis(summary="nothing found")
    assert d.top_hypothesis is None


def test_decision_improvement():
    before = Evaluation(overall=0.6)
    after = Evaluation(overall=0.8)
    dec = Decision(accepted=True, reason="better", before=before, after=after)
    assert abs(dec.improvement - 0.2) < 1e-9


def test_provenance_to_dict():
    before = Evaluation(overall=0.5)
    after = Evaluation(overall=0.7)
    dec = Decision(accepted=True, reason="improved", before=before, after=after)
    p = Provenance(
        artifact_id="a",
        evaluator_id="ev",
        before=before,
        after=after,
        decision=dec,
    )
    d = p.to_dict()
    assert d["artifact_id"] == "a"
    assert d["before"]["overall"] == 0.5
    assert d["after"]["overall"] == 0.7
    assert d["decision"]["accepted"] is True


def test_provenance_no_after():
    before = Evaluation(overall=0.5)
    p = Provenance(artifact_id="a", evaluator_id="ev", before=before)
    d = p.to_dict()
    assert d["after"] is None
    assert d["decision"] is None
