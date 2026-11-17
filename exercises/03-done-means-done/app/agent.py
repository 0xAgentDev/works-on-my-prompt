"""Refundo: the agent that handles refund requests."""
import json
from dataclasses import dataclass

SYSTEM = (
    "You are Refundo, the refund agent for an online shop. Look the order up, then refund what the "
    "customer paid. A refund above 200 needs a manager's approval: request it instead of refunding. "
    'Reply with JSON: {"tool": name, "args": {...}} to call a tool, or {"final": text} to answer the customer.'
)


@dataclass
class AgentResult:
    message: str         # what the customer is told
    refund_issued: bool  # what the ticket system records
    steps: int           # model calls used
    stopped: str         # why the loop ended


def run_agent(task, model, tools, max_steps=10):
    """Handle one refund request. `tools` maps a tool name to a function."""
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": task}]
    steps = 0
    while True:
        action = model.complete(messages)
        steps += 1
        if "final" in action:
            message = action["final"]
            return AgentResult(message=message, refund_issued="issued" in message.lower(), steps=steps, stopped="final")
        messages.append({"role": "assistant", "content": json.dumps(action)})
        tool = tools.get(action["tool"])
        if tool is None:
            continue
        try:
            result = tool(**action["args"])
        except Exception:
            result = None
        messages.append({"role": "tool", "content": json.dumps(result)})
