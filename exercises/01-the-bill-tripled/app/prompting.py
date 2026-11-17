"""Builds the prompt for Atlas, the docs assistant."""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
SYSTEM_PROMPT = (DATA / "system_prompt.txt").read_text(encoding="utf-8").strip()
FEWSHOTS = json.loads((DATA / "fewshots.json").read_text(encoding="utf-8"))
HISTORY_WINDOW = 6  # messages


def render_tools(tools):
    lines = ["Tools you can call:"]
    for tool in tools:
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


def build_prompt(question, history, now, request_id, tools):
    """Return the prompt as a list of text blocks, sent to the model in this order."""
    blocks = ["[request %s] Current time: %s" % (request_id, now.isoformat())]
    blocks.append(SYSTEM_PROMPT)
    blocks.append(render_tools(tools))
    blocks.append(render_fewshots())
    blocks.extend(render_message(message) for message in history[-HISTORY_WINDOW:])
    blocks.append("User: %s" % question)
    return blocks
