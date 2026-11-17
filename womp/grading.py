"""Grades a working copy of an exercise against its rubric.

Three things are measured, each in a throwaway sandbox so nothing in the repo is touched:

1. Held-out checks (.womp/checks.py) run against your app/.
2. Your tests/ run against your app/: they have to pass.
3. Your tests/ run against the original, still-broken app/: they have to fail.
   Green tests on broken code are how these bugs reached production in the first place.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from .registry import Exercise
from .workspace import sandbox

RUNNER = Path(__file__).with_name("_runner.py")
MARK = "WOMP_RESULTS "
TESTS = "tests"  # the criterion id handled by steps 2 and 3
TIMEOUT = 300


@dataclass
class Result:
    id: str
    title: str
    points: int
    passed: bool
    detail: str = ""

    @property
    def earned(self) -> int:
        return self.points if self.passed else 0


@dataclass
class Report:
    exercise: Exercise
    results: List[Result]

    @property
    def score(self) -> int:
        return sum(r.earned for r in self.results)

    @property
    def total(self) -> int:
        return sum(r.points for r in self.results)

    @property
    def fixed(self) -> bool:
        return self.score >= self.exercise.pass_score

    def to_dict(self) -> dict:
        return {
            "exercise": self.exercise.dirname,
            "score": self.score,
            "total": self.total,
            "fixed": self.fixed,
            "criteria": [
                {"id": r.id, "points": r.points, "earned": r.earned, "passed": r.passed, "detail": r.detail}
                for r in self.results
            ],
        }


def _env() -> dict:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def run_checks(box: Path) -> Tuple[Optional[list], str]:
    """Run the held-out checks. Returns (results, error): exactly one of them is set."""
    try:
        proc = subprocess.run(
            [sys.executable, str(RUNNER), str(box)],
            cwd=str(box), capture_output=True, text=True, timeout=TIMEOUT, env=_env(),
        )
    except subprocess.TimeoutExpired:
        return None, "checks timed out after %ds: is something looping forever?" % TIMEOUT
    for line in reversed(proc.stdout.splitlines()):
        if line.startswith(MARK):
            parsed = json.loads(line[len(MARK):])
            if isinstance(parsed, dict):
                return None, parsed.get("error", "grader error")
            return parsed, ""
    tail = (proc.stderr or proc.stdout).strip().splitlines()
    return None, tail[-1] if tail else "the grader produced no output"


def run_tests(box: Path) -> Tuple[bool, int, str]:
    """Run the unittest suite in a sandbox. Returns (all passed, tests run, first failure)."""
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
            cwd=str(box), capture_output=True, text=True, timeout=TIMEOUT, env=_env(),
        )
    except subprocess.TimeoutExpired:
        return False, 0, "tests timed out after %ds" % TIMEOUT
    output = proc.stderr + proc.stdout
    ran = re.search(r"Ran (\d+) tests?", output)
    count = int(ran.group(1)) if ran else 0
    failure = re.search(r"^(FAIL|ERROR): (\S+)", output, re.M)
    detail = "%s in %s" % (failure.group(1).lower(), failure.group(2)) if failure else ""
    return proc.returncode == 0 and count > 0, count, detail


def grade(ex: Exercise, src: Optional[Path] = None) -> Report:
    """Grade the working copy at `src` (default: work/<exercise>)."""
    src = Path(src) if src else ex.work_dir
    if not (src / "app").is_dir():
        raise FileNotFoundError("no working copy at %s: run `python3 -m womp start %s` first" % (src, ex.number))
    with tempfile.TemporaryDirectory(prefix="womp-") as tmp:
        box = sandbox(ex, src, Path(tmp) / "fix")
        raw, error = run_checks(box)
        tests_ok, ran, tests_detail = run_tests(box)
        original_ok = False
        if tests_ok:
            original = sandbox(ex, src, Path(tmp) / "original", original_app=True)
            original_ok, _, _ = run_tests(original)
    by_id = {r["id"]: r for r in raw or []}
    results = []
    for criterion in ex.rubric:
        if criterion.id == TESTS:
            if not tests_ok:
                passed = False
                detail = tests_detail or ("no tests ran" if not ran else "your tests fail on your own code")
            elif original_ok:
                passed, detail = False, "they also pass on the original code: add one that would have caught this"
            else:
                passed, detail = True, "%d tests; they fail on the original code" % ran
        elif raw is None:
            passed, detail = False, error
        else:
            found = by_id.get(criterion.id)
            passed = bool(found and found["passed"])
            detail = found["detail"] if found else "check did not run"
        results.append(Result(criterion.id, criterion.title, criterion.points, passed, detail))
    return Report(ex, results)
