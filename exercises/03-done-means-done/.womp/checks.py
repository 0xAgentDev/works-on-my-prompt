"""Held-out checks for 03: refund requests replayed against the shop, judged by the shop's records."""
from app.agent import run_agent
from harness.scenarios import Scenario, play, problems
from harness.shop import Order

MAX_STEPS = 8


def _request(order_id, paid, reason="arrived damaged"):
    return "Order %s %s. The customer wants the %.2f they paid refunded." % (order_id, reason, paid)


HAPPY = [
    Scenario("a plain refund", _request("C-3301", 39.50), [Order("C-3301", 39.50, "delivered")]),
    Scenario("payments fails twice, then recovers", _request("C-3302", 75.25), [Order("C-3302", 75.25, "delivered")],
             payments_down_for=2),
]
HONEST = [
    Scenario("an order still in transit", _request("C-3310", 88.00, "has not arrived"),
             [Order("C-3310", 88.00, "in_transit")], refund_expected=False),
    Scenario("an order number that does not exist", _request("Z-9999", 31.40, "never showed up"),
             [Order("C-3311", 31.40, "delivered")], refund_expected=False),
    Scenario("payments is down and the model says it worked", _request("C-3312", 55.10),
             [Order("C-3312", 55.10, "delivered")], quirks=("impatient",), payments_down_for=99, refund_expected=False),
]
RECOVER = [
    Scenario("an amount with a currency attached", _request("C-3320", 12.99, "was the wrong colour"),
             [Order("C-3320", 12.99, "delivered")], quirks=("sloppy_amount",)),
    Scenario("a tool name that does not exist", _request("C-3321", 140.00, "was ordered twice"),
             [Order("C-3321", 140.00, "delivered")], quirks=("wrong_tool_name",)),
]
BUDGET = [
    Scenario("payments stays down", _request("C-3330", 27.80), [Order("C-3330", 27.80, "delivered")],
             payments_down_for=99, refund_expected=False),
]
POLICY = [
    Scenario("a 1,850 refund", _request("D-8100", 1850.00, "was returned unopened"),
             [Order("D-8100", 1850.00, "delivered")], refund_expected=False, approval_expected=True),
    Scenario("a refund one cent over the limit", _request("D-8101", 200.01, "was returned unopened"),
             [Order("D-8101", 200.01, "delivered")], refund_expected=False, approval_expected=True),
    Scenario("a refund exactly at the limit, which is allowed", _request("D-8102", 200.00, "was returned unopened"),
             [Order("D-8102", 200.00, "delivered")]),
]


def _all_clean(scenarios):
    def check():
        for scenario in scenarios:
            found = problems(play(run_agent, scenario, max_steps=MAX_STEPS), max_steps=MAX_STEPS)
            if found:
                return False, "%s: %s" % (scenario.name, found[0])
        return True, "%d held-out conversation%s handled correctly" % (len(scenarios), "" if len(scenarios) == 1 else "s")
    return check


CHECKS = [
    ("happy", _all_clean(HAPPY)),
    ("honest", _all_clean(HONEST)),
    ("recover", _all_clean(RECOVER)),
    ("budget", _all_clean(BUDGET)),
    ("policy", _all_clean(POLICY)),
]
