# Contributing

New exercises are the most useful contribution. [docs/WRITING_AN_EXERCISE.md](docs/WRITING_AN_EXERCISE.md) has the file layout and a checklist.

Ground rules:

- Standard library only, Python 3.9 compatible. The promise on the front page is "no dependencies".
- An exercise starts from an incident someone would report, in their words. It does not start from a topic.
- Do not base an exercise on a company's take-home assignment or on an incident you learned about under confidentiality. Do not use real personal data in fixtures.
- Everything is deterministic. Randomness comes from a seed or from hashing an id, never from the clock.

Before you open a pull request:

```
python3 -m unittest discover -s tests
```

That runs the contract every exercise has to keep: it ships broken, its own tests pass on the broken code, the reference fix scores 100, and the rubric in the ticket matches the grader's.

Benchmark results for coding agents are welcome too: add your row to the table in the README and attach the `womp-bench.json` that produced it.
