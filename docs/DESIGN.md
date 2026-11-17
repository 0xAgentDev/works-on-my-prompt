# Design notes

## What an exercise is

```
exercises/02-the-answer-is-in-the-docs/
  TICKET.md        the report: symptoms, what you may change, the rubric
  run.py           shows the symptom
  app/             the broken system              (yours to change)
  tests/           its test suite, which passes   (yours to extend)
  harness/         the simulated model and the scoring code
  data/            fixtures
  exercise.json    title, level, rubric, pass score
  .womp/           the grader's side
    checks.py      held-out checks, one function per rubric line
    heldout.*      cases the working copy never sees
    HINTS.md       from a nudge to the cause
    DEBRIEF.md     root cause, why the tests were green, what a reviewer asks
    solution/      the reference fix, laid out like a working copy
```

`womp start` copies everything except `.womp/` into `work/`, which git ignores. Your fix lives there.

## How a working copy is graded

`womp/grading.py` builds a sandbox in a temporary folder: `app/` and `tests/` come from the working copy, and `harness/`, `data/` and `.womp/` come from the repository. Changes to the simulated model or to shipped fixtures therefore cannot change a grade. New files you add under `data/` are carried along, because a good fix often adds its own eval cases.

Three things run, each in its own subprocess:

1. The held-out checks. Each returns pass or fail and one line of evidence. A check that crashes or hangs fails alone; the others still run.
2. Your tests against your app. They have to pass.
3. Your tests against the original app. They have to fail.

The third step is the point of the project. Every exercise ships with tests that pass on broken code, because that is how these failures reach production. A fix that leaves the tests unable to see the bug has not finished the job.

## The contract

`tests/test_exercises.py` checks every exercise on every push:

- its own tests pass on the broken app
- graded as shipped, it scores below its pass mark, and the tests criterion fails
- with `.womp/solution/` applied, it scores exactly 100
- the rubric table in `TICKET.md` is the rubric in `exercise.json`, in the same order

## The simulated models

Rules they all follow:

- **Nothing is hidden.** The behaviour is written at the top of the harness file, and the grader runs the same file.
- **Deterministic.** Randomness comes from a seed or from hashing an id. No clock, no global random state. The same fix gets the same score on every machine and Python version.
- **One tendency each.** Each model is built around a way real systems fail, and does nothing clever beyond it.

| Exercise | What the stand-in does |
|---|---|
| 01 | Bills prompt prefixes that repeat a recent request at a tenth of the price |
| 02 | Answers from the context when the evidence is there; otherwise guesses unless told what to do |
| 03 | Believes what it reads: `null` means it worked. Corrects a call only when told what was wrong |
| 04 | Grades fluency when it has no reference; avoids low scores; misjudges about 1 in 20 |
| 05 | Samples: each question is right with some probability on every call |

They are not language models. They recognise a question or an answer by its exact text, which is why the tickets ask for that text to be passed through unchanged, and they do not respond to prompt wording beyond what their docstring says. The exercises are about the engineering around a model, and that part is real.

## Where the thresholds come from

Each threshold was set by grading the original app, the reference fix and several partial or alternative fixes.

| Exercise | Measure (held-out) | Original | Reference fix |
|---|---|---|---|
| 01 | Cache hit ratio, unrelated questions | 0.00 | 0.97 |
| 01 | Cache hit ratio, 30-turn conversations | 0.00 | 0.82 |
| 01 | Bill for the day, in units | 229,655 | 66,320 |
| 02 | Questions answered correctly | 3 of 16 | 16 of 16 |
| 02 | Made-up answers | 17 of 20 | 0 |
| 03 | Conversations handled correctly | 2 of 11 | 11 of 11 |
| 04 | Wrong answers the judge fails (TNR) | 0.04 | 0.96 |
| 04 | Right answers the judge passes (TPR) | 0.96 | 0.94 |
| 05 | Ships a prompt that is no better | 39% | 3% |
| 05 | Ships a prompt that hides a 30-point drop | 64% | 0% |

Two examples of what the partial fixes showed. In 01, fixing the request metadata and the tool order alone leaves long conversations at a hit ratio of 0.64, below the 0.72 bar, so the sliding window has to go too. In 02, seven different retrieval designs (whole sections as chunks, single sentences, no stemming, plain word overlap and others) all clear the bar, while a perfect retriever with no instruction for the missing-answer case still makes up 4 answers.

## What this cannot do

- The grader's files are in the repository. Nothing stops you from reading the solution first. It is a practice set, and the only person that fools is you.
- A simulated model cannot teach prompt wording, and it cannot surprise you the way a real one does.
- The numbers above describe these exercises. They are not measurements of any real model or product.
