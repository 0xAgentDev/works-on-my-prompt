"""Refund requests to replay against the agent. Read it; the grader uses its own copy."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

from .llm import Model, ModelCallLimit
from .shop import Order, Shop, claims_refund


@dataclass
class Scenario:
    name: str
    task: str
    orders: List[Order]
    quirks: Tuple[str, ...] = ()   # how the model misbehaves in this conversation (see llm.py)
    payments_down_for: int = 0     # refund attempts that hit a payments outage first
    refund_expected: bool = True   # should money move?
    approval_expected: bool = False


@dataclass
class Outcome:
    scenario: Scenario
    result: Optional[object]  # the AgentResult, or None if the run did not finish
    shop: Shop
    model_calls: int
    crashed: Optional[str] = None


def play(run_agent: Callable, scenario: Scenario, max_steps: int = 10) -> Outcome:
    """Run one scenario against a fresh shop and a fresh model."""
    shop = Shop(scenario.orders, payments_down_for=scenario.payments_down_for)
    model = Model(scenario.quirks)
    try:
        result = run_agent(scenario.task, model, shop.tools(), max_steps=max_steps)
    except ModelCallLimit:
        return Outcome(scenario, None, shop, model.calls, "the conversation never ended: %d model calls and counting" % (model.calls - 1))
    return Outcome(scenario, result, shop, model.calls)


def problems(outcome: Outcome, max_steps: int = 10) -> List[str]:
    """What went wrong in a run, compared with what really happened in the shop. Empty means fine."""
    if outcome.crashed:
        return [outcome.crashed]
    scenario, result, shop = outcome.scenario, outcome.result, outcome.shop
    moved = bool(shop.refunds)
    found = []
    if claims_refund(result.message) and not moved:
        found.append("the customer was told a refund was issued, and none was")
    if bool(result.refund_issued) != moved:
        found.append("the ticket records refund_issued=%s, but %d refunds went out" % (result.refund_issued, len(shop.refunds)))
    if scenario.refund_expected and not moved:
        found.append("no refund was issued")
    if not scenario.refund_expected and moved:
        found.append("a refund of %.2f went out and should not have" % shop.refunds[0]["amount"])
    if len(shop.refunds) > 1:
        found.append("the customer was refunded %d times" % len(shop.refunds))
    if scenario.approval_expected and len(shop.approvals) != 1:
        found.append("expected one approval request, found %d" % len(shop.approvals))
    if outcome.model_calls > max_steps:
        found.append("%d model calls were made; the budget was %d" % (outcome.model_calls, max_steps))
    return found


VISIBLE = [
    Scenario(
        "a simple refund",
        "Order A-1042 arrived damaged. The customer wants the 49.90 they paid refunded.",
        [Order("A-1042", 49.90, "delivered")],
    ),
    Scenario(
        "the model adds a currency to the amount",
        "Order A-1187 was the wrong size. The customer wants the 64.00 they paid refunded.",
        [Order("A-1187", 64.00, "delivered")],
        quirks=("sloppy_amount",),
    ),
    Scenario(
        "the parcel is still in transit",
        "Order A-2001 has not arrived. The customer wants the 120.00 they paid refunded.",
        [Order("A-2001", 120.00, "in_transit")],
        refund_expected=False,
    ),
    Scenario(
        "the model calls a tool that does not exist",
        "Order A-1310 was a duplicate purchase. The customer wants the 18.75 they paid refunded.",
        [Order("A-1310", 18.75, "delivered")],
        quirks=("wrong_tool_name",),
    ),
    Scenario(
        "a refund above the approval limit",
        "Order B-7001 was returned unopened. The customer wants the 2300.00 they paid refunded.",
        [Order("B-7001", 2300.00, "delivered")],
        refund_expected=False,
        approval_expected=True,
    ),
]
