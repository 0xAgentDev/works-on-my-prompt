# 05 · Is B better?

**Channel:** #prompt-changes  **Severity:** SEV-3 (a decision, not an outage)

> **Product manager:** Prompt B scored 81.7% on the eval and prompt A scored 76.7%. That is five points. Can we ship B today? Last month's winner made production worse, and I still do not know why.

## What you know

- The support-ticket classifier runs on prompt A. Prompt B is the candidate.
- The eval set has 60 questions in five slices: billing, shipping, returns, account and technical.
- The model samples its answers, so the same question can come out right on one run and wrong on the next.
- `decide(lab)` in `app/compare.py` makes the call. Today it runs every question once with each prompt and ships B if B's score is higher.
- A decision may spend up to 1,200 graded model calls (`lab.budget`).
- The test suite passes.

## See it

    python3 run.py

## Your job

Make `decide(lab)` return a decision you would defend in front of that product manager. Change `app/compare.py`.

Keep `decide(lab)` returning a `Decision`:

- `ship`: replace A with B, or not
- `delta`: your estimate of B's accuracy minus A's
- `interval`: a 95% confidence interval for `delta`, as `(low, high)`
- `slices`: your estimate of that difference for each slice
- `reason`: one sentence a product manager can read

`harness/lab.py` has `simulate()`, which builds experiments where you set the truth, and `truth()`, which reports it. Use them to find out how often your rule is wrong.

## How it is graded

| Points | Criterion |
|---|---|
| 30 | Does not ship a prompt that is no better, or worse |
| 20 | Ships a prompt that really is better |
| 25 | Catches a regression hidden inside a better average |
| 15 | Reports an interval that contains the truth |
| 10 | Your tests pass on the fix and fail on the original |

80 points fixes it. The grader runs your rule on 400 simulated experiments whose truth it knows, and counts how often the rule is right.
