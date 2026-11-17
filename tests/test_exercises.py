"""The contract every exercise has to keep.

It ships broken with a green test suite, and its reference fix scores 100. If either stops
being true, the exercise is lying to the people who practice on it.
"""
import re
import tempfile
import unittest
from pathlib import Path

from womp.grading import TESTS, grade, run_tests
from womp.registry import load_all
from womp.workspace import materialize, sandbox


class ExerciseContract(unittest.TestCase):
    def test_there_are_exercises(self):
        self.assertGreaterEqual(len(load_all()), 1)

    def test_files_and_rubric(self):
        for ex in load_all():
            with self.subTest(ex.dirname):
                for name in ("TICKET.md", "run.py", "app", "tests", "harness"):
                    self.assertTrue((ex.path / name).exists(), name)
                for name in ("checks.py", "HINTS.md", "DEBRIEF.md", "solution"):
                    self.assertTrue((ex.private / name).exists(), name)
                self.assertEqual(sum(c.points for c in ex.rubric), 100)
                self.assertEqual(ex.rubric[-1].id, TESTS)
                self.assertLessEqual(max(len(c.title) for c in ex.rubric), 58)

    def test_ticket_shows_the_real_rubric(self):
        for ex in load_all():
            with self.subTest(ex.dirname):
                ticket = (ex.path / "TICKET.md").read_text(encoding="utf-8")
                rows = re.findall(r"^\| (\d+) \| (.+?) \|$", ticket, re.M)
                self.assertEqual(rows, [(str(c.points), c.title) for c in ex.rubric])
                self.assertIn("%d points fixes it" % ex.pass_score, ticket)

    def test_starts_broken_with_green_tests(self):
        for ex in load_all():
            with self.subTest(ex.dirname), tempfile.TemporaryDirectory() as tmp:
                work = materialize(ex, Path(tmp) / "work")
                passed, ran, detail = run_tests(sandbox(ex, work, Path(tmp) / "box"))
                self.assertTrue(passed, "the shipped tests must pass on the broken app: %s" % detail)
                report = grade(ex, src=work)
                self.assertLess(report.score, ex.pass_score, report.to_dict())
                self.assertFalse(any(r.passed for r in report.results if r.id == TESTS))

    def test_reference_fix_scores_100(self):
        for ex in load_all():
            with self.subTest(ex.dirname), tempfile.TemporaryDirectory() as tmp:
                work = materialize(ex, Path(tmp) / "work", solved=True)
                report = grade(ex, src=work)
                failed = [(r.id, r.detail) for r in report.results if not r.passed]
                self.assertEqual(report.score, 100, failed)


if __name__ == "__main__":
    unittest.main()
