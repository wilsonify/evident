# evident

A small, composable toolkit for building **evidence-driven applications**.

```
Observe
   ↓
Evaluate
   ↓
Diagnose
   ↓
Intervene
   ↓
Verify
   ↓
Keep or Reject
```

---

## What problem does this solve?

Many applications need to:

1. **observe** something real (a document, audio, config, log, sensor reading)
2. **measure** how well an artifact agrees with that reality
3. **identify** likely problems
4. **propose or perform** a bounded improvement
5. **independently measure** the result
6. **keep the improvement only if evidence shows it helped**
7. **retain enough provenance** to explain what happened

`evident` makes this pattern reusable across completely different domains,
without forcing you into a heavyweight framework.

---

## Why isn't this just a test suite?

A test suite tells you _pass_ or _fail_.
`evident` measures _how well_, tracks _why_ something might be wrong,
attempts an _improvement_, and _independently verifies_ whether the
improvement actually helped before accepting it.

## Why isn't this just an optimization library?

Optimization libraries minimise a loss function; they don't care _why_ the
loss improved or whether the improvement is trustworthy.
`evident` is about **provenance and accountability**: an improvement is only
accepted when an **independent evaluator** (not the improver) confirms it.

## Where does Bayesian inference fit?

Bayesian belief updating, active learning, and Bayesian optimisation are
_strategies_ – they can live in the `evaluator`, `diagnoser`, or `improver`
slots without changing the core loop.

The first version of `evident` does **not** include Bayesian inference.
The substrate is designed so that adding it later requires no changes
to the core.

## Where does AI fit?

AI can be the `improver` (e.g. an LLM that edits a document) or the
`evaluator` (e.g. a classifier that scores an artifact).

The framework's only constraint: **the improver and the evaluator must be
independent**.  If the same AI both proposes and accepts an improvement,
the framework provides no safety net.

## What remains application-specific?

Everything domain-specific stays in _your_ code:

| Slot | Your responsibility |
|------|-------------------|
| `artifact` | the thing you want to improve |
| `evidence` | the ground truth or validation suite |
| `evaluator` | how you score an artifact against evidence |
| `improver` | how you propose a candidate |
| `policy` | what "better" means for your application |
| `diagnoser` | optional – converts an Evaluation into actionable hints |

---

## Quick start

```python
from evident import EvidenceLoop, Evaluation
from evident.policies import strictly_better

def evaluate(artifact, evidence):
    score = 1.0 if artifact["text"] == evidence["expected"] else 0.0
    return Evaluation(overall=score, passed=score >= 0.9)

def improve(artifact, diagnosis):
    return {"text": artifact["text"].strip().lower()}

loop = EvidenceLoop(
    artifact={"text": "  Hello World  "},
    evidence={"expected": "hello world"},
    evaluator=evaluate,
    improver=improve,
    policy=strictly_better,
)
result, history = loop.run()
print(result)                        # {'text': 'hello world'}
print(history[0].decision.accepted)  # True
```

---

## Installation

```bash
pip install evident
```

---

## Bootstrap a new project

```bash
evidence init my-project
cd my-project
pip install -e ".[dev]"
pytest
```

This creates:

```
my-project/
  pyproject.toml
  README.md
  src/my_project/
    artifact.py    <- define your artifact
    evidence.py    <- define your evidence
    evaluate.py    <- independent scoring  <- edit this first
    improve.py     <- proposes a candidate
    policy.py      <- accepts or rejects
  tests/
    test_my_project.py
```

---

## Core concepts

### Evaluation

Separates **measurement**, **interpretation**, and **decision**:

```python
Evaluation(
    overall=0.947,
    metrics={"timing_accuracy": 0.981, "coverage": 0.932},
    passed=True,
    label="word-overlap",
)
```

### The fundamental invariant

```
improver says "better"
      ≠
framework accepts "better"
```

Only independent evaluation causes acceptance:

```
candidate -> independent evaluator -> evaluation -> policy -> accept/reject
```

### Provenance

Every cycle produces a `Provenance` record that can be serialised to JSON:

```json
{
  "artifact_id": "my-doc",
  "evaluator_id": "word-overlap-v1",
  "before": {"overall": 0.41},
  "after":  {"overall": 0.87},
  "decision": {"accepted": true, "improvement": 0.46}
}
```

---

## Examples

| Example | Domain | What it shows |
|---------|--------|---------------|
| `examples/document_extraction/` | Text | Word-overlap scoring, normalisation as improvement |
| `examples/config_validation/` | Config | Pass/fail assertion, missing-key repair |

Run either example:

```bash
python examples/document_extraction/run.py
python examples/config_validation/run.py
```

---

## API reference

### `EvidenceLoop`

```python
loop = EvidenceLoop(
    artifact=...,
    evidence=...,
    evaluator=evaluate,   # (artifact, evidence) -> Evaluation
    improver=improve,     # (artifact, diagnosis) -> candidate
    policy=policy,        # (before, after) -> Decision
    diagnoser=None,       # optional: (evaluation) -> Diagnosis
    max_iterations=10,
)
result, history = loop.run()
```

### `improve_and_verify`

Single-cycle version of the loop, returns `(artifact, Provenance)`.

### Bundled policies (`evident.policies`)

| Policy | Accepts when |
|--------|-------------|
| `strictly_better` | `after.overall > before.overall` |
| `must_pass` | `after.passed is True` |
| `threshold(min)` | `after.overall >= min` |

---

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check src tests
```

---

## Architecture

```
evident/
  models.py      - immutable dataclasses (Evaluation, Decision, Provenance, ...)
  core.py        - plain functions: evaluate(), compare(), improve_and_verify()
  loop.py        - EvidenceLoop convenience wrapper
  policies.py    - bundled acceptance policies
  cli.py         - `evidence init` command
```

No databases, no service infrastructure, no plugin registries.
Read the source in one sitting.

---

## License

MIT
