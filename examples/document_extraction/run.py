"""Example: document extraction validated against source evidence.

A simple text extractor is evaluated against expected text.
The improver fixes the extracted text when it disagrees with the evidence.

Run this example:
    python examples/document_extraction/run.py
"""

from __future__ import annotations

from dataclasses import dataclass

from evident import Diagnosis, Evaluation, EvidenceLoop
from evident.policies import strictly_better


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


@dataclass
class ExtractedDocument:
    """An artifact: text extracted from a source document."""

    text: str


@dataclass
class SourceEvidence:
    """Evidence: the ground-truth text from the source."""

    expected_text: str


# ---------------------------------------------------------------------------
# Evaluator (independent from extractor)
# ---------------------------------------------------------------------------


def evaluate(doc: ExtractedDocument, evidence: SourceEvidence) -> Evaluation:
    """Score how closely the extracted text matches the expected text."""
    extracted = doc.text.strip()
    expected = evidence.expected_text.strip()

    if not expected:
        return Evaluation(overall=1.0, passed=True, label="empty evidence")

    # Word-level overlap
    extracted_words = set(extracted.lower().split())
    expected_words = set(expected.lower().split())
    if not expected_words:
        return Evaluation(overall=1.0, passed=True)

    precision = len(extracted_words & expected_words) / max(len(extracted_words), 1)
    recall = len(extracted_words & expected_words) / len(expected_words)
    f1 = 2 * precision * recall / max(precision + recall, 1e-9)

    return Evaluation(
        overall=f1,
        metrics={"precision": precision, "recall": recall, "f1": f1},
        passed=f1 >= 0.8,
        label="word-overlap",
    )


# ---------------------------------------------------------------------------
# Improver
# ---------------------------------------------------------------------------


def improve(doc: ExtractedDocument, diagnosis: Diagnosis) -> ExtractedDocument:
    """Simulate an improved extraction (strips extra whitespace, normalises case)."""
    # A real improver might re-run OCR, call an LLM, etc.
    return ExtractedDocument(text=" ".join(doc.text.lower().split()))


# ---------------------------------------------------------------------------
# Demo run
# ---------------------------------------------------------------------------


def run() -> None:
    artifact = ExtractedDocument(text="  Hello   World  extra   words  ")
    evidence = SourceEvidence(expected_text="hello world")

    loop = EvidenceLoop(
        artifact=artifact,
        evidence=evidence,
        evaluator=evaluate,
        improver=improve,
        policy=strictly_better,
        artifact_id="extracted-doc",
        evidence_id="source-text",
        evaluator_id="word-overlap-evaluator",
    )

    result, history = loop.run()

    print("=== Document Extraction Example ===")
    for i, p in enumerate(history):
        print(f"\nIteration {i + 1}:")
        print(f"  before : {p.before.overall:.3f}")
        print(f"  after  : {p.after.overall:.3f}")
        print(f"  accepted: {p.decision.accepted} – {p.decision.reason}")

    print(f"\nFinal text: {result.text!r}")


if __name__ == "__main__":
    run()
