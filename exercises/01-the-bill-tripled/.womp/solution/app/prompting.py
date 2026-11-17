"""Builds the prompt for Atlas, the docs assistant."""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
SYSTEM_PROMPT = (DATA / "system_prompt.txt").read_text(encoding="utf-8").strip()
FEWSHOTS = json.loads((DATA / "fewshots.json").read_text(encoding="utf-8"))
HISTORY_BUDGET = 1500  # tokens of conversation kept in the prompt
TRIM_STEP = 8          # when over budget, drop this many of the oldest messages at once
KEEP_RECENT = 4        # never trim into the most recent messages


def render_tools(tools):
    lines = ["Tools you can call:"]
    for tool in sorted(tools, key=lambda tool: tool["name"]):  # one order on every worker
        lines.append("- %s(%s): %s" % (tool["name"], tool["params"], tool["description"]))
    return "\n".join(lines)


def render_fewshots():
    parts = ["Examples:"]
    for shot in FEWSHOTS:
        parts.append("User: %s\nAtlas: %s" % (shot["user"], shot["assistant"]))
    return "\n\n".join(parts)


def render_message(message):
    speaker = "User" if message["role"] == "user" else "Atlas"
    return "%s: %s" % (speaker, message["text"])


def stable_history(history):
    """Trim old messages in coarse steps.

    A window that slides by one message per turn changes the start of the history on every
    request, so nothing after the static prefix is ever cached. Cutting several messages at
    once keeps the history identical to the previous turn's, plus the new messages, until
    the next cut.
    """
    sizes = [len(render_message(message).split()) for message in history]
    start = 0
    while sum(sizes[start:]) > HISTORY_BUDGET and len(history) - (start + TRIM_STEP) >= KEEP_RECENT:
        start += TRIM_STEP
    return history[start:]


def build_prompt(question, history, now, request_id, tools):
    """Return the prompt as a list of text blocks, sent to the model in this order.

    Order is by how often a block changes: never (system prompt, tools, examples), once per
    turn (history, which only grows), every request (time, request id, question).
    """
    blocks = [SYSTEM_PROMPT, render_tools(tools), render_fewshots()]
    blocks.extend(render_message(message) for message in stable_history(history))
    blocks.append("[request %s] Current time: %s" % (request_id, now.isoformat()))
    blocks.append("User: %s" % question)
    return blocks
