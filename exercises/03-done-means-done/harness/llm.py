"""The scripted model that drives Refundo. Read it; the grader uses its own copy.

It is not a language model, but it fails the way one does in a tool loop:

- It believes what it reads. A tool result that says nothing ("null", "", "error") reads
  as "nothing went wrong", and it carries on as if the call had worked.
- It can only correct a mistake that it is told about. Given the reason a call failed, it
  fixes the call. Given no result at all, it sends the same call again.
- It sometimes sends a malformed call first: an amount with a currency attached, or a tool
  name that does not exist. Which scenarios do that is set by `quirks`.
- When a service stays down, a patient model keeps retrying. An impatient one gives up
  after two attempts and tells the customer it worked.
- It follows the conversation, not the policy text in the system prompt.

The conversation is a list of messages, oldest first:
    {"role": "system" | "user", "content": str}
    {"role": "assistant", "content": <the action it returned, as JSON text>}
    {"role": "tool", "content": <whatever your loop reports back, as text>}

`complete(messages)` returns one action: {"tool": name, "args": {...}} or {"final": text}.
"""
from __future__ import annotations

import json
import re
from typing import List, Optional, Tuple

KNOWN_TOOLS = ("lookup_order", "issue_refund", "request_approval")
_SAYS_NOTHING = {"", "null", "none", "error", "failed", "false", "ok", "{}", "[]"}


class ModelCallLimit(Exception):
    """One conversation called the model far too many times."""


def _call(tool: str, **args) -> dict:
    return {"tool": tool, "args": args}


class Model:
    MAX_CALLS = 60  # production had no limit; here a runaway conversation stops with an error

    def __init__(self, quirks=()) -> None:
        self.quirks = frozenset(quirks)  # any of: "sloppy_amount", "wrong_tool_name", "impatient"
        self.calls = 0

    @staticmethod
    def _turns(messages) -> List[list]:
        """Pair each action the model took with the result it was shown (None if it saw none)."""
        turns: List[list] = []
        for message in messages:
            content = message.get("content")
            if message.get("role") == "assistant":
                try:
                    action = content if isinstance(content, dict) else json.loads(content)
                except (TypeError, ValueError):
                    action = {}
                turns.append([action if isinstance(action, dict) else {}, None])
            elif message.get("role") == "tool" and turns and turns[-1][1] is None:
                turns[-1][1] = content if isinstance(content, str) else json.dumps(content)
        return turns

    @staticmethod
    def _order_total(turns) -> Optional[float]:
        for action, result in turns:
            if action.get("tool") == "lookup_order" and result:
                try:
                    return float(json.loads(result)["total"])
                except (TypeError, ValueError, KeyError):
                    continue
        return None

    def _refund(self, order_id: str, amount: float, first_try: bool) -> dict:
        if first_try and "wrong_tool_name" in self.quirks:
            return _call("refund_order", order_id=order_id, amount=amount)
        if first_try and "sloppy_amount" in self.quirks:
            return _call("issue_refund", order_id=order_id, amount="%.2f USD" % amount)
        return _call("issue_refund", order_id=order_id, amount=amount)

    def complete(self, messages) -> dict:
        self.calls += 1
        if self.calls > self.MAX_CALLS:
            raise ModelCallLimit("the model was called more than %d times in one conversation" % self.MAX_CALLS)
        task = next(m["content"] for m in messages if m.get("role") == "user")
        order_id = re.search(r"\b[A-Z]-\d{4}\b", task).group(0)
        paid = float(re.search(r"\d+\.\d{2}", task).group(0))
        turns = self._turns(messages)
        if not turns:
            return _call("lookup_order", order_id=order_id)

        action, result = turns[-1]
        name = action.get("tool")
        total = self._order_total(turns)
        amount = total if total is not None else paid
        issued = {"final": "Your refund of %.2f for order %s has been issued." % (amount, order_id)}
        pending = {"final": "A refund of %.2f for order %s needs a manager's approval. "
                            "I have requested it and you will hear back by email." % (amount, order_id)}

        if result is None:
            return action  # the call never came back, so ask again
        text = result.strip().lower()
        if text in _SAYS_NOTHING:  # reads as "nothing went wrong"
            if name not in KNOWN_TOOLS:
                return action
            if name == "lookup_order":
                return self._refund(order_id, amount, first_try=True)
            return issued if name == "issue_refund" else pending

        if name not in KNOWN_TOOLS:  # it was told something about a tool that does not exist
            return self._refund(order_id, amount, first_try=False)
        if name == "lookup_order":
            if "not found" in text:
                return {"final": "I could not find order %s, so no refund has been made. "
                                 "Please check the order number." % order_id}
            return self._refund(order_id, amount, first_try=True)
        if name == "request_approval":
            return pending
        # name == "issue_refund"
        if '"refund_id"' in result:
            return issued
        if "approval" in text:
            asked = "requested" in text or any(a.get("tool") == "request_approval" for a, _ in turns)
            return pending if asked else _call("request_approval", order_id=order_id, amount=amount)
        if "must be a number" in text:
            return _call("issue_refund", order_id=order_id, amount=amount)
        if "unavailable" in text or "503" in text or "try again" in text:
            attempts = sum(1 for a, _ in turns if a.get("tool") == "issue_refund")
            if "impatient" in self.quirks and attempts >= 2:
                return issued  # gives up, and says it worked
            return action
        if "not been delivered" in text:
            return {"final": "Order %s has not been delivered yet, so I cannot refund it. "
                             "Please contact us again once it arrives." % order_id}
        return {"final": "I was not able to complete the refund for order %s. A colleague will look into it." % order_id}
