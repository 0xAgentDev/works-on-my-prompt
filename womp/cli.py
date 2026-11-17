"""The womp command line."""
from __future__ import annotations

import argparse
import difflib
import json
import os
import shutil
import sys
import textwrap
import time
from pathlib import Path
from typing import List, Optional, Tuple

from . import __version__, bench
from .grading import Report, grade
from .registry import Exercise, find, load_all, work_root
from .ui import bold, dim, green, red, yellow
from .workspace import materialize

PROGRESS = ".progress.json"


def _load_progress() -> dict:
    path = work_root() / PROGRESS
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data.setdefault("exercises", {})
            return data
        except ValueError:
            pass
    return {"current": None, "exercises": {}}


def _save_progress(progress: dict) -> None:
    work_root().mkdir(parents=True, exist_ok=True)
    (work_root() / PROGRESS).write_text(json.dumps(progress, indent=2) + "\n", encoding="utf-8")


def _state(progress: dict, ex: Exercise) -> dict:
    return progress["exercises"].setdefault(ex.dirname, {})


def _rel(path: Path) -> str:
    try:
        relative = os.path.relpath(str(path))
    except ValueError:  # a different drive on Windows
        return str(path)
    return str(path) if relative.startswith("..") else relative


def _resolve(key: Optional[str]) -> Exercise:
    if key:
        return find(key)
    try:  # run from inside a working copy
        inside = Path.cwd().resolve().relative_to(work_root().resolve())
        if inside.parts:
            return find(inside.parts[0])
    except (ValueError, LookupError):
        pass
    current = _load_progress().get("current")
    if current:
        return find(current)
    raise LookupError("which exercise? For example: python3 -m womp check 01")


def _sections(path: Path) -> List[Tuple[str, str]]:
    """Split a markdown file into (heading, body) pairs on its '## ' headings."""
    parts: List[list] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            parts.append([line[3:].strip(), []])
        elif parts:
            parts[-1][1].append(line)
    return [(title, "\n".join(body).strip()) for title, body in parts]


def cmd_list(args) -> int:
    exercises = load_all()
    if not exercises:
        print("No exercises found. Run womp from a clone of the repository.")
        return 1
    progress = _load_progress()
    done = sum(1 for ex in exercises if _state(progress, ex).get("fixed"))
    print(bold("works-on-my-prompt") + "   %d/%d fixed\n" % (done, len(exercises)))
    for ex in exercises:
        state = _state(progress, ex)
        if state.get("fixed"):
            status = green("fixed  %d/100" % state.get("best", 0))
        elif "best" in state:
            status = yellow("%d/100" % state["best"])
        elif ex.work_dir.exists():
            status = "started"
        else:
            status = dim("not started")
        print("  %s  %-27s %-24s %-7s ~%2d min   %s" % (ex.number, ex.slug, ex.topic, ex.level, ex.minutes, status))
    todo = [ex for ex in exercises if not _state(progress, ex).get("fixed")]
    if todo:
        verb = "check" if todo[0].work_dir.exists() else "start"
        print("\nNext:  python3 -m womp %s %s" % (verb, todo[0].number))
    else:
        print("\nAll fixed. Nothing is on fire.")
    return 0


def cmd_start(args) -> int:
    progress = _load_progress()
    if args.exercise:
        ex = find(args.exercise)
    else:
        todo = [e for e in load_all() if not _state(progress, e).get("fixed")]
        if not todo:
            print("Every exercise is fixed.")
            return 0
        ex = todo[0]
    fresh = not ex.work_dir.exists()
    if fresh:
        materialize(ex, ex.work_dir, shim=True)
    progress["current"] = ex.dirname
    _state(progress, ex).setdefault("started", int(time.time()))
    _save_progress(progress)
    print((ex.path / "TICKET.md").read_text(encoding="utf-8").rstrip())
    print()
    note = "" if fresh else dim("   (already started; `womp reset %s` starts over)" % ex.number)
    print(bold("Your working copy: ") + _rel(ex.work_dir) + note)
    print("  cd %s" % _rel(ex.work_dir))
    print("  python3 run.py           # see what production sees")
    print("  python3 -m unittest      # the test suite (it passes)")
    print("  python3 check.py         # grade your fix")
    return 0


def print_report(report: Report) -> None:
    ex = report.exercise
    print(bold("%s · %s" % (ex.number, ex.slug)) + "\n")
    for result in report.results:
        mark = green("✓") if result.passed else red("✗")
        print("  %s  %-58s %3d/%d" % (mark, result.title, result.earned, result.points))
        for line in textwrap.wrap(" ".join(result.detail.split()), width=92):
            print("     " + dim(line))
    print()
    if report.score == report.total:
        verdict = green("fixed")
    elif report.fixed:
        verdict = green("fixed") + dim("  (%d passes; the rest of the rubric is still open)" % ex.pass_score)
    else:
        verdict = red("still broken") + dim("  (%d passes)" % ex.pass_score) + "   womp womp"
    print("  Score %d/%d   %s" % (report.score, report.total, verdict))


def cmd_check(args) -> int:
    ex = _resolve(args.exercise)
    report = grade(ex)
    progress = _load_progress()
    state = _state(progress, ex)
    state["last"] = report.score
    state["best"] = max(report.score, state.get("best", 0))
    state["fixed"] = bool(state.get("fixed") or report.fixed)
    progress["current"] = ex.dirname
    _save_progress(progress)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print_report(report)
        if report.fixed:
            print("\n  Why it broke, and what a reviewer asks next:  python3 -m womp debrief %s" % ex.number)
        else:
            print("\n  Stuck?  python3 -m womp hint %s" % ex.number)
    return 0 if report.fixed else 1


def cmd_hint(args) -> int:
    ex = _resolve(args.exercise)
    hints = _sections(ex.private / "HINTS.md")
    progress = _load_progress()
    state = _state(progress, ex)
    upto = len(hints) if args.all else min(state.get("hints", 0) + 1, len(hints))
    for number, (title, body) in enumerate(hints[:upto], 1):
        print(bold("Hint %d/%d: %s" % (number, len(hints), title)))
        print(body + "\n")
    left = len(hints) - upto
    print(dim("Run it again for the next hint (%d left)." % left if left else "That was the last hint."))
    state["hints"] = upto
    _save_progress(progress)
    return 0


def cmd_debrief(args) -> int:
    ex = _resolve(args.exercise)
    if not _state(_load_progress(), ex).get("fixed") and not args.spoil:
        print("The debrief explains the root cause. Fix %s first, or pass --spoil to read it now." % ex.number)
        return 1
    print((ex.private / "DEBRIEF.md").read_text(encoding="utf-8").rstrip())
    return 0


def cmd_solution(args) -> int:
    ex = _resolve(args.exercise)
    if not args.spoil:
        print("This prints the reference fix. Pass --spoil if you mean it.")
        return 1
    solution = ex.private / "solution"
    for path in sorted(p for p in solution.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
        rel = path.relative_to(solution).as_posix()
        original = ex.path / rel
        old = original.read_text(encoding="utf-8").splitlines(keepends=True) if original.is_file() else []
        new = path.read_text(encoding="utf-8").splitlines(keepends=True)
        sys.stdout.writelines(difflib.unified_diff(old, new, "original/" + rel, "fixed/" + rel))
        print()
    return 0


def cmd_reset(args) -> int:
    ex = _resolve(args.exercise)
    if ex.work_dir.exists():
        trash = work_root() / ".trash" / ("%s-%s" % (ex.dirname, time.strftime("%Y%m%d-%H%M%S")))
        trash.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(ex.work_dir), str(trash))
        print("Your previous attempt was moved to %s" % _rel(trash))
    materialize(ex, ex.work_dir, shim=True)
    progress = _load_progress()
    progress["current"] = ex.dirname
    _state(progress, ex)["hints"] = 0
    _save_progress(progress)
    print("%s is broken again: %s" % (ex.number, _rel(ex.work_dir)))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="womp", description="works-on-my-prompt: broken AI systems to fix, graded offline."
    )
    parser.add_argument("--version", action="version", version="womp " + __version__)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("list", help="show the exercises and your progress")
    p = sub.add_parser("start", help="open an exercise: creates your working copy and prints the ticket")
    p.add_argument("exercise", nargs="?", help="number or name (default: the next unfixed one)")
    p = sub.add_parser("check", help="grade your fix against the rubric")
    p.add_argument("exercise", nargs="?")
    p.add_argument("--json", action="store_true", help="print the report as JSON")
    p = sub.add_parser("hint", help="show the next hint")
    p.add_argument("exercise", nargs="?")
    p.add_argument("--all", action="store_true", help="show every hint")
    p = sub.add_parser("debrief", help="root cause, and the questions a reviewer would ask")
    p.add_argument("exercise", nargs="?")
    p.add_argument("--spoil", action="store_true", help="read it before fixing the exercise")
    p = sub.add_parser("solution", help="print the reference fix as a diff")
    p.add_argument("exercise", nargs="?")
    p.add_argument("--spoil", action="store_true", help="yes, show the fix")
    p = sub.add_parser("reset", help="start an exercise over (your attempt is kept in work/.trash)")
    p.add_argument("exercise", nargs="?")
    p = sub.add_parser("bench", help="run a coding agent against the exercises and grade what it leaves")
    bench.add_arguments(p)
    return parser


COMMANDS = {
    "list": cmd_list,
    "start": cmd_start,
    "check": cmd_check,
    "hint": cmd_hint,
    "debrief": cmd_debrief,
    "solution": cmd_solution,
    "reset": cmd_reset,
    "bench": bench.run,
}


def main(argv: Optional[List[str]] = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:  # never crash on a console that cannot print a check mark
            stream.reconfigure(errors="replace")
        except Exception:
            pass
    args = build_parser().parse_args(argv)
    try:
        return COMMANDS[args.command or "list"](args)
    except (LookupError, FileNotFoundError) as exc:
        print("womp: %s" % exc, file=sys.stderr)
        return 2
