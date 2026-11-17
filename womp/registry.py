"""Finds the exercises on disk and reads their metadata."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

ROOT = Path(os.environ.get("WOMP_HOME") or Path(__file__).resolve().parent.parent)
EXERCISES = ROOT / "exercises"
PRIVATE = ".womp"  # the grader's side of an exercise: held-out checks, hints, debrief, solution


def work_root() -> Path:
    """Where working copies live. Kept out of git so your fixes stay yours."""
    return Path(os.environ.get("WOMP_WORK") or ROOT / "work")


@dataclass(frozen=True)
class Criterion:
    id: str
    title: str
    points: int


@dataclass(frozen=True)
class Exercise:
    dirname: str
    path: Path
    title: str
    summary: str
    topic: str
    level: str
    minutes: int
    pass_score: int
    rubric: Tuple[Criterion, ...]

    @property
    def number(self) -> str:
        return self.dirname.split("-", 1)[0]

    @property
    def slug(self) -> str:
        return self.dirname.split("-", 1)[1]

    @property
    def private(self) -> Path:
        return self.path / PRIVATE

    @property
    def work_dir(self) -> Path:
        return work_root() / self.dirname


def load_all() -> List[Exercise]:
    exercises = []
    if not EXERCISES.is_dir():
        return exercises
    for folder in sorted(EXERCISES.iterdir()):
        meta_file = folder / "exercise.json"
        if not meta_file.is_file():
            continue
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        exercises.append(
            Exercise(
                dirname=folder.name,
                path=folder,
                title=meta["title"],
                summary=meta["summary"],
                topic=meta["topic"],
                level=meta["level"],
                minutes=int(meta["minutes"]),
                pass_score=int(meta.get("pass_score", 80)),
                rubric=tuple(Criterion(c["id"], c["title"], int(c["points"])) for c in meta["rubric"]),
            )
        )
    return exercises


def find(key: str) -> Exercise:
    """Look an exercise up by number ("1", "01"), slug, or any unique part of its name."""
    key = key.strip().lower()
    exercises = load_all()
    for ex in exercises:
        if key in (ex.dirname, ex.slug, ex.number, ex.number.lstrip("0")):
            return ex
    matches = [ex for ex in exercises if key and key in ex.dirname]
    if len(matches) == 1:
        return matches[0]
    known = ", ".join(ex.number for ex in exercises) or "none found"
    raise LookupError(f"no exercise matches {key!r} (available: {known})")
