# 04 · The judge says yes

**Channel:** #quality  **Severity:** SEV-2 (the quality number cannot be trusted)

> **Head of support:** The dashboard says 97% of Parcelo's answers are good. My team read 60 of last week's answers and marked 21 of them wrong. Either my team is wrong or your judge is.

## What you know

- Parcelo is the support assistant. Every answer it gives is graded by an LLM judge (`app/judge.py`), and the dashboard shows the share that pass.
- The support leads labelled 60 answers by hand. They are in `data/labeled.jsonl`, each with the reference answer for its question.
- Nobody has compared the judge with human labels before. `agreement()` in `app/metrics.py` was never written.
- The judge model is simulated. `harness/llm.py` describes how it grades. A small share of its replies come back unusable, as with any API.
- The test suite passes.

## See it

    python3 run.py

## Your job

1. Write `agreement(judge_verdicts, human_verdicts)` in `app/metrics.py`, so the judge can be measured against people.
2. Fix the judge in `app/judge.py` until it agrees with them.

Keep `judge(example, model)`: it returns `True` for pass and `False` for fail, and it does not raise. An example is a dict with `question`, `answer`, `reference` and, in the labelled file, `human_label`.

Put the answer and the reference into the prompt word for word. The simulated judge needs them to know what it is grading.

## How it is graded

| Points | Criterion |
|---|---|
| 20 | agreement() reports TPR, TNR and kappa correctly |
| 30 | The judge fails the answers people marked wrong |
| 20 | The judge passes the answers people marked right |
| 20 | A reply that cannot be read never counts as a pass |
| 10 | Your tests pass on the fix and fail on the original |

80 points fixes it. The grader uses 80 labelled answers you have not seen. At least 85% of the answers people marked wrong have to fail, and at least 90% of the ones they marked right have to pass.
