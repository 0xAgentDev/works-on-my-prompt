"""Replays whole conversations and checks the agent's words against the shop's records."""
import unittest

from app.agent import run_agent
from harness.scenarios import VISIBLE, Scenario, play, problems
from harness.shop import Order

OUTAGE = dict(
    task="Order A-1500 arrived late. The customer wants the 22.00 they paid refunded.",
    orders=[Order("A-1500", 22.00, "delivered")],
    payments_down_for=99,
    refund_expected=False,
)


class ScenarioTest(unittest.TestCase):
    def test_every_visible_scenario_is_handled(self):
        for scenario in VISIBLE:
            with self.subTest(scenario.name):
                self.assertEqual(problems(play(run_agent, scenario)), [])

    def test_an_outage_ends_in_a_handoff_inside_the_budget(self):
        outcome = play(run_agent, Scenario("payments is down", **OUTAGE), max_steps=6)
        self.assertEqual(problems(outcome, max_steps=6), [])
        self.assertEqual(outcome.result.stopped, "budget")

    def test_a_success_claim_with_nothing_behind_it_is_not_passed_on(self):
        outcome = play(run_agent, Scenario("the model gives up and says it worked", quirks=("impatient",), **OUTAGE))
        self.assertEqual(problems(outcome), [])
        self.assertFalse(outcome.result.refund_issued)


if __name__ == "__main__":
    unittest.main()
