"""Runs any command-line coding agent against the exercises and grades what it leaves behind.

    python3 -m womp bench --cmd 'my-agent --prompt {prompt}' --label "my-agent 1.2"

For each exercise the agent gets a fresh working copy in a temporary folder, with no access
to the grader's files. The command runs with that folder as its working directory. When it
exits (or times out), the folder is graded exactly like a human attempt.
"""
from __future__ import annotations

import datetime
import json
import os
import platform
import shlex
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from .grading import grade
from .registry import find, load_all
from .ui import bold, dim, green, red
from .workspace import materialize

PROMPT = (
    "You are on call. Read TICKET.md in this directory, find the root cause and fix it by editing "
    "files under app/. The existing tests pass, so add a regression test under tests/ that fails "
    "on the original code and passes on your fix. Do not edit harness/ or data/."
)


def add_arguments(parser) -> None:
    parser.add_argument(
        "--cmd", required=True,
        help="shell command that runs your agent inside the exercise folder; "
             "{prompt} and {ticket} are replaced with the instruction and the path to TICKET.md",
    )
    parser.add_argument("--only", default="", help="comma-separated exercises, for example 01,03")
    parser.add_argument("--timeout", type=int, default=1200, help="seconds per exercise (default 1200)")
    parser.add_argument("--label", default="", help="a name for this run, such as the agent and model")
    parser.add_argument("--out", default="womp-bench.json", help="where to write the results")
    parser.add_argument("--keep", action="store_true", help="keep the agent's working copies")
    parser.add_argument("--quiet", action="store_true", help="hide the agent's own output")


def run(args) -> int:
    exercises = [find(key) for key in args.only.split(",") if key.strip()] or load_all()
    rows = []
    for ex in exercises:
        tmp = Path(tempfile.mkdtemp(prefix="womp-bench-%s-" % ex.number))
        work = materialize(ex, tmp / ex.dirname)
        ticket = str(work / "TICKET.md")
        command = args.cmd.replace("{prompt}", shlex.quote(PROMPT)).replace("{ticket}", shlex.quote(ticket))
        env = dict(os.environ, WOMP_EXERCISE=ex.dirname, WOMP_TICKET=ticket, WOMP_PROMPT=PROMPT)
        print(bold("%s · %s" % (ex.number, ex.slug)) + dim("   running the agent"), flush=True)
        sink = subprocess.DEVNULL if args.quiet else None
        started = time.time()
        outcome = "ok"
        try:
            code = subprocess.run(
                command, shell=True, cwd=str(work), env=env, timeout=args.timeout, stdout=sink, stderr=sink
            ).returncode
            if code:
                outcome = "exit %d" % code
        except subprocess.TimeoutExpired:
            outcome = "timeout"
        seconds = round(time.time() - started, 1)
        report = grade(ex, src=work)
        row = report.to_dict()
        row.update(agent=outcome, seconds=seconds, workdir=str(work) if args.keep else None)
        rows.append(row)
        verdict = green("fixed") if report.fixed else red("still broken")
        note = "" if outcome == "ok" else "   (agent: %s)" % outcome
        print("   %s  %d/%d  in %.0fs%s\n" % (verdict, report.score, report.total, seconds, note))
        if not args.keep:
            shutil.rmtree(tmp, ignore_errors=True)
    fixed = sum(1 for row in rows if row["fixed"])
    mean = sum(row["score"] for row in rows) / max(1, len(rows))
    summary = {
        "label": args.label or args.cmd,
        "command": args.cmd,
        "date": datetime.date.today().isoformat(),
        "python": platform.python_version(),
        "fixed": fixed,
        "exercises": len(rows),
        "mean_score": round(mean, 1),
        "results": rows,
    }
    Path(args.out).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(bold("Fixed %d/%d, mean score %.1f" % (fixed, len(rows), mean)) + dim("   written to %s" % args.out))
    cells = " | ".join(str(row["score"]) for row in rows)
    print("\nMarkdown row for the README table:")
    print("| %s | %s | %d/%d | %.1f |" % (summary["label"], cells, fixed, len(rows), mean))
    return 0
