import unittest

from app.compare import Decision, decide
from harness.lab import simulate


class DecideTest(unittest.TestCase):
    def test_returns_a_decision(self):
        decision = decide(simulate(effect=0.3, seed=1))
        self.assertIsInstance(decision, Decision)
        self.assertIsInstance(decision.reason, str)

    def test_ships_a_prompt_that_is_far_better(self):
        self.assertTrue(decide(simulate(effect=0.3, seed=1)).ship)

    def test_keeps_a_when_b_is_far_worse(self):
        self.assertFalse(decide(simulate(effect=-0.3, seed=1)).ship)

    def test_stays_inside_the_budget(self):
        lab = simulate(seed=1)
        decide(lab)
        self.assertLessEqual(lab.calls, lab.budget)


if __name__ == "__main__":
    unittest.main()
