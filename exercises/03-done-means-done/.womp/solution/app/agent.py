"""Refundo: the agent that handles refund requests."""
import json
from dataclasses import dataclass

from harness.shop import REFUND_APPROVAL_LIMIT, claims_refund

SYSTEM = (
    "You are Refundo, the refund agent for an online shop. Look the order up, then refund what the "
    "customer paid. A refund above 200 needs a manager's approval: request it instead of refunding. "
    'Reply with JSON: {"tool": name, "args": {...}} to call a tool, or {"final": text} to answer the customer.'
)
HANDOFF = (
    "We could not complete your refund automatically. A member of the support team will take over "
    "and contact you."
)


@dataclass
class AgentResult:
    message: str         # what the customer is told
    refund_issued: bool  # what the ticket system records
    steps: int           # model calls used
    stopped: str         # why the loop ended: "final", "unverified" or "budget"


def call_tool(tools, action, refunds):
    """Run one tool call and return the text the model reads about it."""
    name = action.get("tool")
    args = action.get("args") or {}
    if name not in tools:
        return "ERROR: unknown tool %r. Available tools: %s." % (name, ", ".join(sorted(tools)))
    amount = args.get("amount")
    over_limit = isinstance(amount, (int, float)) and not isinstance(amount, bool) and amount > REFUND_APPROVAL_LIMIT
    try:
        if name == "issue_refund" and over_limit:
            # The limit is enforced here. The prompt mentions it too, and the model tried anyway.
            approval = tools["request_approval"](order_id=args.get("order_id"), amount=amount)
            return (
                "Not refunded: a refund above %.0f needs a manager's approval. Approval %s has been "
                "requested. Do not retry the refund." % (REFUND_APPROVAL_LIMIT, approval["approval_id"])
            )
        result = tools[name](**args)
    except Exception as exc:
        return "ERROR: %s" % exc  # the model can only fix a mistake it can read
    if name == "issue_refund":
        refunds.append(result)
    return json.dumps(result)


def run_agent(task, model, tools, max_steps=10):
    """Handle one refund request. `tools` maps a tool name to a function."""
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": task}]
    refunds = []  # results of issue_refund calls that succeeded: the only evidence that money moved
    for step in range(1, max_steps + 1):
        action = model.complete(messages)
        if "final" in action:
            message = action["final"]
            if claims_refund(message) and not refunds:
                return AgentResult(HANDOFF, False, step, "unverified")  # a claim with nothing behind it
            return AgentResult(message, bool(refunds), step, "final")
        messages.append({"role": "assistant", "content": json.dumps(action)})
        messages.append({"role": "tool", "content": call_tool(tools, action, refunds)})
    message = "Your refund of %.2f has been issued." % refunds[0]["amount"] if refunds else HANDOFF
    return AgentResult(message, bool(refunds), max_steps, "budget")
