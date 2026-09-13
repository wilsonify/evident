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

## Quick start

```python
from evident import improve_and_verify, Evaluation
from evident.policies import strictly_better

# The evaluator captures its own evidence via closure.
# No evidence parameter needed in the framework API.
lyrics = load_lyrics("song.lrc")
audio = load_audio("song.mp3")

def evaluate(candidate):
    return score_lyrics_against_audio(candidate, lyrics, audio)

def improve(artifact, diagnosis):
    return fix_timing(artifact, diagnosis)

result, decision = improve_and_verify(
    artifact=artifact,
    evaluator=evaluate,
    improver=improve,
    policy=strictly_better,
)
```

For iterative improvement:

```python
from evident import EvidenceLoop

loop = EvidenceLoop(
    artifact=artifact,
    evaluator=evaluate,   # (artifact) -> Evaluation
    improver=improve,     # (artifact, diagnosis) -> candidate
    policy=strictly_better,
)
result, history = loop.run()
```

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
| `evaluator` | `(artifact) -> Evaluation` – captures its own evidence via closure |
| `improver` | `(artifact, diagnosis) -> candidate` |
| `policy` | `(before, after) -> Decision` – what "better" means |
| `diagnoser` | optional `(evaluation) -> Diagnosis` |

---

## The fundamental invariant

```
improver says "better"
      ≠
framework accepts "better"
```

Only independent evaluation causes acceptance:

```
candidate -> independent evaluator -> evaluation -> policy -> accept/reject
```

---

## Multi-metric policies

A policy is a plain Python function.
No DSL, no configuration, no framework-specific abstractions.

```python
def require_both_improve(before: Evaluation, after: Evaluation) -> Decision:
    """Accept only when ALL metrics improve."""
    both = all(
        after.metrics.get(k, 0) > before.metrics.get(k, 0)
        for k in before.metrics
    )
    reason = "all metrics improved" if both else "some metrics did not improve"
    return Decision(accepted=both, reason=reason, before=before, after=after)
```

---

## Provenance (opt-in)

By default `improve_and_verify` returns `(artifact, decision)`.
Pass `provenance=True` to also get a structured record:

```python
result, decision, prov = improve_and_verify(
    artifact, evaluate, improve, policy, provenance=True
)
print(prov.to_dict())
# {
#   "artifact_id": "...",
#   "evaluator_id": "...",
#   "before": {"overall": 0.5, ...},
#   "after":  {"overall": 0.8, ...},
#   "decision": {"accepted": true, "improvement": 0.3}
# }
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
    evidence.py    <- define your evidence type
    evaluate.py    <- make_evaluator(evidence) -> (artifact) -> Evaluation
    improve.py     <- proposes a candidate
    policy.py      <- accepts or rejects
  tests/
    test_my_project.py
```

---

## Examples

| Example | Domain | What it shows |
|---------|--------|---------------|
| `examples/document_extraction/` | Text | Word-overlap scoring with closure-based evidence |
| `examples/config_validation/` | Config | Pass/fail assertion, missing-key repair |

```bash
python examples/document_extraction/run.py
python examples/config_validation/run.py
```

---

## API reference

### `improve_and_verify`

```python
result, decision = improve_and_verify(
    artifact,
    evaluator,   # (artifact) -> Evaluation
    improver,    # (artifact, diagnosis) -> candidate
    policy,      # (before, after) -> Decision
)
```

### `EvidenceLoop`

```python
loop = EvidenceLoop(
    artifact=...,
    evaluator=evaluate,
    improver=improve,
    policy=policy,
    diagnoser=None,       # optional: (evaluation) -> Diagnosis
    max_iterations=10,
)
result, history = loop.run()
```

### `compare`

```python
decision = compare(before, after, policy)
```

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
  core.py        - plain functions: compare(), improve_and_verify()
  loop.py        - EvidenceLoop convenience wrapper
  policies.py    - bundled acceptance policies
  cli.py         - `evidence init` command
```

No databases, no service infrastructure, no plugin registries.
Read the source in one sitting.

---

## License

MIT
