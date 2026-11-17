"""End-to-end checks of the command line, run against a throwaway work folder."""
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from womp.registry import find

ROOT = Path(__file__).resolve().parent.parent
FAKE_AGENT = Path(__file__).with_name("fake_agent.py")


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="womp-cli-"))
        self.addCleanup(shutil.rmtree, str(self.tmp), ignore_errors=True)
        self.work = self.tmp / "work"
        self.env = dict(os.environ, WOMP_WORK=str(self.work), NO_COLOR="1", PYTHONDONTWRITEBYTECODE="1")
        self.ex = find("01")

    def womp(self, *args, cwd=ROOT):
        return subprocess.run(
            [sys.executable, "-m", "womp"] + list(args), cwd=str(cwd), env=self.env, capture_output=True, text=True
        )

    def test_list_shows_exercises_and_progress(self):
        out = self.womp()
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn(self.ex.slug, out.stdout)
        self.assertIn("not started", out.stdout)

    def test_version_matches_the_package_metadata(self):
        declared = re.search(r'^version = "(.+?)"', (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.M).group(1)
        self.assertEqual(self.womp("--version").stdout.strip(), "womp " + declared)

    def test_unknown_exercise_is_a_clean_error(self):
        out = self.womp("check", "99")
        self.assertEqual(out.returncode, 2)
        self.assertIn("no exercise matches", out.stderr)

    def test_start_fix_check_reset(self):
        copy = self.work / self.ex.dirname
        started = self.womp("start", "01")
        self.assertEqual(started.returncode, 0, started.stderr)
        self.assertIn(self.ex.title, started.stdout)
        for name in ("app", "tests", "harness", "TICKET.md", "run.py", "check.py"):
            self.assertTrue((copy / name).exists(), name)
        self.assertFalse((copy / ".womp").exists(), "the grader's files must stay out of the working copy")

        broken = self.womp("check")  # no argument: the exercise started last
        self.assertEqual(broken.returncode, 1, broken.stdout + broken.stderr)
        self.assertIn("still broken", broken.stdout)
        self.assertEqual(self.womp("debrief", "01").returncode, 1)
        self.assertIn("Hint 1/", self.womp("hint", "01").stdout)

        shutil.copytree(self.ex.private / "solution", copy, dirs_exist_ok=True)
        report = json.loads(self.womp("check", "01", "--json").stdout)
        self.assertEqual((report["score"], report["fixed"]), (100, True))
        shim = subprocess.run([sys.executable, "check.py"], cwd=str(copy), env=self.env, capture_output=True, text=True)
        self.assertEqual(shim.returncode, 0, shim.stdout + shim.stderr)
        self.assertEqual(self.womp("debrief", "01").returncode, 0)
        self.assertIn("fixed", self.womp("list").stdout)

        self.assertEqual(self.womp("reset", "01").returncode, 0)
        self.assertEqual(self.womp("check", "01").returncode, 1)
        self.assertTrue(any((self.work / ".trash").iterdir()), "reset keeps the previous attempt")

    def test_solution_needs_a_spoiler_flag(self):
        self.assertEqual(self.womp("solution", "01").returncode, 1)
        shown = self.womp("solution", "01", "--spoil")
        self.assertEqual(shown.returncode, 0)
        self.assertIn("+++ fixed/app/", shown.stdout)

    @unittest.skipIf(os.name == "nt", "the fake agent command line is POSIX shell")
    def test_bench_grades_what_an_agent_leaves_behind(self):
        agent = "%s %s" % (shlex.quote(sys.executable), shlex.quote(str(FAKE_AGENT)))
        for mode, fixed, score in (("solve", 1, 100), ("noop", 0, None)):
            out_file = self.tmp / ("bench-%s.json" % mode)
            run = self.womp("bench", "--only", "01", "--quiet", "--out", str(out_file), "--cmd", agent + " " + mode)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            summary = json.loads(out_file.read_text(encoding="utf-8"))
            self.assertEqual(summary["fixed"], fixed)
            if score is not None:
                self.assertEqual(summary["results"][0]["score"], score)


if __name__ == "__main__":
    unittest.main()
