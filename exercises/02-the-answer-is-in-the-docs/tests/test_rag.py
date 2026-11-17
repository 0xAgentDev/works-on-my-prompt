import unittest
from pathlib import Path

from app import rag
from harness.evaluate import HANDBOOK, evaluate
from harness.llm import load_items

DATA = Path(__file__).resolve().parent.parent / "data"


class RagTest(unittest.TestCase):
    def setUp(self):
        self.index = rag.build_index(HANDBOOK)

    def test_retrieve_returns_a_few_text_chunks(self):
        chunks = rag.retrieve("A VPN session expires after how many hours?", self.index)
        self.assertTrue(1 <= len(chunks) <= 6)
        self.assertTrue(all(isinstance(chunk, str) for chunk in chunks))

    def test_prompt_holds_the_question_and_the_excerpts(self):
        prompt = rag.build_prompt("Is this a question?", ["first excerpt", "second excerpt"])
        for part in ("Is this a question?", "first excerpt", "second excerpt"):
            self.assertIn(part, prompt)

    def test_offline_eval_passes(self):
        scores = evaluate(rag, load_items(DATA / "eval_questions.jsonl"))
        self.assertGreaterEqual(scores.accuracy, 0.9)


if __name__ == "__main__":
    unittest.main()
