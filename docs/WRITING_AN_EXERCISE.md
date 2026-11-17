# Writing an exercise

## Start from an incident

An exercise is a report someone would file, in their words: "the bill tripled", "the bot told a customer we offer pet insurance". If you find yourself starting from a topic ("an exercise about embeddings"), look for the incident first. The topic follows from the cause.

Do not base an exercise on a company's take-home assignment, or on an incident you know about under confidentiality. Do not use real personal data in fixtures.

## Checklist

1. **The tests are green on the broken code.** The shipped `tests/` must pass before the fix. They test what the original author thought mattered.
2. **The symptom is visible.** `python3 run.py` shows, in a few lines, what the reporter saw.
3. **The contract is stated.** The ticket names the functions and signatures that must stay, and anything the simulated model needs passed through unchanged.
4. **The stand-in is documented first.** Write the docstring at the top of the harness file before the code: how the model behaves, as a short list. Keep it deterministic: seeds and hashes, no clock.
5. **Visible and held-out cases differ.** `run.py` and `data/` show some cases. `.womp/` holds others, built the same way with different seeds, questions or scenarios.
6. **The rubric has three to five lines plus the tests line.** Points sum to 100. The last line has the id `tests`, is worth 10 and reads "Your tests pass on the fix and fail on the original". Titles stay under 59 characters. Each check returns one line of evidence with numbers in it.
7. **There is a reference fix.** `.womp/solution/` mirrors a working copy: the fixed `app/` files and at least one new test file that fails on the original code. It must score exactly 100.
8. **Thresholds were tried against more than one fix.** Grade the original, the reference and at least two partial or alternative fixes. A sound fix of a different design should pass. A fix that addresses only the easy half should not.
9. **Hints go from a nudge to the cause.** `HINTS.md` is a list of `## ` sections; `womp hint` shows one more each time.
10. **The debrief has four parts.** `## What was wrong`, `## Why the tests were green`, `## How you know it stays fixed`, `## What a reviewer asks next`. Put measured numbers in the first part.

## Files

```
exercises/NN-short-name/
  exercise.json
  TICKET.md
  run.py
  app/__init__.py  app/<module>.py
  tests/__init__.py  tests/test_<module>.py
  harness/__init__.py  harness/<stand-in>.py
  data/...
  .womp/checks.py  .womp/HINTS.md  .womp/DEBRIEF.md
  .womp/solution/app/<module>.py
  .womp/solution/tests/test_<something new>.py
```

`exercise.json`:

```json
{
  "title": "The bill tripled",
  "summary": "One sentence, as the reporter would put it.",
  "topic": "cost · prompt caching",
  "level": "easy",
  "minutes": 25,
  "pass_score": 75,
  "rubric": [
    {"id": "stable_prefix", "title": "Unrelated requests share a cached prefix", "points": 30},
    {"id": "tests", "title": "Your tests pass on the fix and fail on the original", "points": 10}
  ]
}
```

`.womp/checks.py` exposes `CHECKS`, a list of `(criterion_id, function)`. Each function returns `(passed, detail)`. Import the app the way a user's test would (`from app.module import thing`); the grader runs the file with the sandbox as the working directory.

## Verify

```
python3 -m unittest discover -s tests
```

The contract tests pick the new exercise up on their own.
