import datetime
import unittest

from app.prompting import build_prompt
from harness import provider, traffic

NOW = datetime.datetime(2026, 3, 3, 9, 30, 0)


class CacheTest(unittest.TestCase):
    def test_unrelated_requests_share_a_cached_prefix(self):
        bill = provider.replay(build_prompt, traffic.single_questions(40, seed=1))
        self.assertGreaterEqual(bill.hit_ratio, 0.85)

    def test_tool_order_does_not_change_the_prompt(self):
        one = build_prompt("q", [], NOW, "req-1", list(traffic.TOOLS))
        other = build_prompt("q", [], NOW, "req-1", list(reversed(traffic.TOOLS)))
        self.assertEqual(one, other)

    def test_long_conversations_stay_cached(self):
        bill = provider.replay(build_prompt, traffic.conversations(2, 30, seed=2))
        self.assertGreaterEqual(bill.hit_ratio, 0.72)


if __name__ == "__main__":
    unittest.main()
