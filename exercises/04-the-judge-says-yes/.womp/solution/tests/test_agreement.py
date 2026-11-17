"""The comparison nobody had run: the judge against the answers people labelled."""
import unittest
from pathlib import Path

from app.judge import judge, parse_verdict
from app.metrics import agreement
from harness.llm import JudgeModel, load_examples

DATA = Path(__file__).resolve().parent.parent / "data"


class Unusable:
    def complete(self, prompt):
        return "I am unable to grade this response."


class AgreementTest(unittest.TestCase):
    def setUp(self):
        self.examples = load_examples(DATA / "labeled.jsonl")

    def test_judge_agrees_with_people_on_the_labelled_answers(self):
        model = JudgeModel(self.examples)
        verdicts = [judge(example, model) for example in self.examples]
        report = agreement(verdicts, [example["human_label"] == "pass" for example in self.examples])
        self.assertGreaterEqual(report["tnr"], 0.85, "wrong answers are getting through")
        self.assertGreaterEqual(report["tpr"], 0.90, "right answers are being failed")

    def test_agreement_on_verdicts_worked_out_by_hand(self):
        report = agreement([True, True, False, False], [True, False, False, False])
        self.assertEqual(report["n"], 4)
        self.assertAlmostEqual(report["tpr"], 1.0)
        self.assertAlmostEqual(report["tnr"], 2 / 3)
        self.assertAlmostEqual(report["kappa"], 0.5)

    def test_a_judge_that_passes_everything_has_kappa_zero(self):
        report = agreement([True] * 6, [True, True, True, True, False, False])
        self.assertAlmostEqual(report["kappa"], 0.0)
        self.assertAlmostEqual(report["tnr"], 0.0)

    def test_an_unusable_reply_is_not_a_pass(self):
        self.assertFalse(judge(self.examples[0], Unusable()))

    def test_a_fail_that_mentions_pass_is_still_a_fail(self):
        self.assertIs(parse_verdict("FAIL: the answer does not pass."), False)
        self.assertIs(parse_verdict("PASS"), True)
        self.assertIsNone(parse_verdict("The tone is passable."))


if __name__ == "__main__":
    unittest.main()
