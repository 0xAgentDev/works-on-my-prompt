import unittest
from pathlib import Path

from app.judge import judge
from app.metrics import pass_rate
from harness.llm import JudgeModel, load_examples

DATA = Path(__file__).resolve().parent.parent / "data"


class JudgeTest(unittest.TestCase):
    def setUp(self):
        self.examples = load_examples(DATA / "labeled.jsonl")
        self.model = JudgeModel(self.examples)

    def test_judge_returns_a_boolean(self):
        self.assertIsInstance(judge(self.examples[0], self.model), bool)

    def test_an_answer_that_matches_the_reference_passes(self):
        example = next(e for e in self.examples if e["answer"] == e["reference"])
        self.assertTrue(judge(example, self.model))

    def test_pass_rate(self):
        self.assertEqual(pass_rate([True, True, False, True]), 0.75)
        self.assertEqual(pass_rate([]), 0.0)


if __name__ == "__main__":
    unittest.main()
