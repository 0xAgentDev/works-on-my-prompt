"""Lays out working copies and grading sandboxes.

An exercise folder holds four kinds of files:

  app/, tests/        yours: the broken system and its (passing) tests
  harness/, data/     the world around the system: simulated model, tools, fixtures
  TICKET.md, run.py   the report of what is wrong, and a script that shows it
  .womp/              the grader's side: held-out checks, hints, debrief, solution

A working copy gets everything except .womp/. A grading sandbox takes app/ and tests/
from the working copy and everything else from the repo, so edits to harness/ or to the
shipped fixtures cannot change a grade.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from .registry import PRIVATE, ROOT, Exercise

USER_OWNED = ("app", "tests")
GRADER_OWNED = ("harness", "data")
TOP_FILES = ("TICKET.md", "run.py")
_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")

_CHECK_SHIM = '''#!/usr/bin/env python3
"""Grade this exercise from here: python3 check.py"""
import subprocess
import sys

raise SystemExit(subprocess.call([sys.executable, "-m", "womp", "check", {number!r}], cwd={root!r}))
'''


def _copy_dir(src: Path, dst: Path) -> None:
    if src.is_dir():
        shutil.copytree(src, dst, ignore=_IGNORE, dirs_exist_ok=True)


def materialize(ex: Exercise, dest: Path, solved: bool = False, shim: bool = False) -> Path:
    """Create a working copy of an exercise at `dest` (optionally with the reference fix applied)."""
    dest.mkdir(parents=True, exist_ok=True)
    for name in USER_OWNED + GRADER_OWNED:
        _copy_dir(ex.path / name, dest / name)
    for name in TOP_FILES:
        if (ex.path / name).is_file():
            shutil.copy2(ex.path / name, dest / name)
    if solved:
        _copy_dir(ex.private / "solution", dest)
    if shim:
        (dest / "check.py").write_text(_CHECK_SHIM.format(number=ex.number, root=str(ROOT)), encoding="utf-8")
    return dest


def sandbox(ex: Exercise, src: Path, dest: Path, original_app: bool = False) -> Path:
    """Build a grading sandbox at `dest` from the working copy at `src`.

    With original_app=True the app comes from the repo (still broken) while the tests come
    from the working copy: that is how the grader asks "would your tests have caught it?".
    """
    for name in GRADER_OWNED:
        _copy_dir(ex.path / name, dest / name)
    user_data = src / "data"
    if user_data.is_dir():  # new fixture files are welcome; shipped ones always win
        for item in user_data.rglob("*"):
            rel = item.relative_to(user_data)
            target = dest / "data" / rel
            if item.is_file() and not target.exists() and "__pycache__" not in rel.parts:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)
    _copy_dir((ex.path if original_app else src) / "app", dest / "app")
    _copy_dir(src / "tests", dest / "tests")
    _copy_dir(ex.private, dest / PRIVATE)
    return dest
