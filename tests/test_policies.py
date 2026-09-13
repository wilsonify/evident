"""Tests for bundled policies."""

from evident.models import Evaluation
from evident.policies import must_pass, strictly_better, threshold


def test_strictly_better_accepts():
    before = Evaluation(overall=0.5)
    after = Evaluation(overall=0.7)
    d = strictly_better(before, after)
    assert d.accepted is True


def test_strictly_better_rejects_equal():
    before = Evaluation(overall=0.7)
    after = Evaluation(overall=0.7)
    d = strictly_better(before, after)
    assert d.accepted is False


def test_strictly_better_rejects_worse():
    before = Evaluation(overall=0.9)
    after = Evaluation(overall=0.5)
    d = strictly_better(before, after)
    assert d.accepted is False


def test_must_pass_accepts_when_passed():
    before = Evaluation(overall=0.4, passed=False)
    after = Evaluation(overall=0.9, passed=True)
    d = must_pass(before, after)
    assert d.accepted is True


def test_must_pass_rejects_when_failed():
    before = Evaluation(overall=0.9, passed=True)
    after = Evaluation(overall=0.8, passed=False)
    d = must_pass(before, after)
    assert d.accepted is False


def test_threshold_accepts_at_minimum():
    policy = threshold(0.8)
    before = Evaluation(overall=0.5)
    after = Evaluation(overall=0.8)
    d = policy(before, after)
    assert d.accepted is True


def test_threshold_rejects_below():
    policy = threshold(0.9)
    before = Evaluation(overall=0.5)
    after = Evaluation(overall=0.8)
    d = policy(before, after)
    assert d.accepted is False
