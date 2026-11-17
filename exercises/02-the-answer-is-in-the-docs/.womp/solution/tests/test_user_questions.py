"""The eval the original system never had: questions the way staff type them."""
import unittest
from pathlib import Path

from app import rag
from harness.evaluate import HANDBOOK, evaluate
from harness.llm import load_items, normalize, sentences

DATA = Path(__file__).resolve().parent.parent / "data"


class UserQuestionsTest(unittest.TestCase):
    def setUp(self):
        self.scores = evaluate(rag, load_items(DATA / "user_reports.jsonl"))

    def test_reported_questions_are_answered_from_the_handbook(self):
        self.assertEqual(self.scores.accuracy, 1.0, [row.reply for row in self.scores.rows if row.outcome != "correct"])

    def test_nothing_is_made_up(self):
        self.assertEqual([row.reply for row in self.scores.wrong], [])

    def test_no_handbook_sentence_is_cut_by_chunking(self):
        chunks = [normalize(chunk) for chunk in rag.build_index(HANDBOOK)]
        for sentence in sentences(HANDBOOK):
            self.assertTrue(any(normalize(sentence) in chunk for chunk in chunks), sentence)


if __name__ == "__main__":
    unittest.main()
