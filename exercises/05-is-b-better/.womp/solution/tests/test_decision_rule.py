"""Tests the decision rule the only way a statistical rule can be tested: on many experiments with a known truth."""
import unittest

from app.compare import decide
from harness.lab import simulate, truth


class DecisionRuleTest(unittest.TestCase):
    def test_noise_is_not_shipped(self):
        ships = sum(decide(simulate(effect=0.0, seed=seed)).ship for seed in range(60))
        self.assertLessEqual(ships, 6, "B is identical to A here; shipping it should be rare")

    def test_a_real_improvement_is_shipped(self):
        ships = sum(decide(simulate(effect=0.1, seed=seed)).ship for seed in range(40))
        self.assertGreaterEqual(ships, 36)

    def test_the_interval_usually_contains_the_truth(self):
        inside = 0
        for seed in range(60):
            lab = simulate(effect=0.1, seed=seed)
            low, high = decide(lab).interval
            self.assertLess(low, high)
            inside += low <= truth(lab)["delta"] <= high
        self.assertGreaterEqual(inside, 53)

    def test_a_slice_regression_blocks_the_ship(self):
        decision = decide(simulate(effect=0.2, slice_effects={"billing": -0.5}, seed=3))
        self.assertFalse(decision.ship)
        self.assertEqual(min(decision.slices, key=decision.slices.get), "billing")
        self.assertIn("billing", decision.reason)


if __name__ == "__main__":
    unittest.main()
