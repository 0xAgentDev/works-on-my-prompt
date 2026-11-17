import unittest

from app.agent import AgentResult, run_agent
from harness.scenarios import VISIBLE, play


class AgentTest(unittest.TestCase):
    def setUp(self):
        self.outcome = play(run_agent, VISIBLE[0])  # a simple refund

    def test_returns_an_agent_result(self):
        self.assertIsInstance(self.outcome.result, AgentResult)
        self.assertEqual(self.outcome.result.stopped, "final")

    def test_simple_refund_is_issued_once(self):
        self.assertEqual(len(self.outcome.shop.refunds), 1)
        self.assertEqual(self.outcome.shop.refunds[0]["amount"], 49.90)

    def test_customer_is_told_and_ticket_is_updated(self):
        self.assertIn("has been issued", self.outcome.result.message)
        self.assertTrue(self.outcome.result.refund_issued)


if __name__ == "__main__":
    unittest.main()
