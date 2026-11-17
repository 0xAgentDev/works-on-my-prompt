"""Held-out checks for 01. Each returns (passed, detail). The traffic seeds differ from run.py."""
import json
from pathlib import Path

from app.prompting import build_prompt
from harness import provider, traffic

DATA = Path(__file__).resolve().parent.parent / "data"
BUDGET = 77000  # units for the held-out day: last week's bill for the same traffic, plus 10%


def _norm(text):
    return " ".join(text.split())


def check_stable_prefix():
    bill = provider.replay(build_prompt, traffic.single_questions(150, seed=4101))
    return bill.hit_ratio >= 0.85, "cache hit ratio %.2f on 150 unrelated questions (need 0.85)" % bill.hit_ratio


def check_complete():
    system = _norm((DATA / "system_prompt.txt").read_text(encoding="utf-8"))
    shots = json.loads((DATA / "fewshots.json").read_text(encoding="utf-8"))
    requests = traffic.single_questions(5, seed=4202) + traffic.conversations(2, 30, seed=4203)
    for request in requests:
        blocks = build_prompt(request.question, list(request.history), request.now, request.request_id, list(request.tools))
        prompt = _norm("\n".join(blocks))
        missing = []
        if system not in prompt:
            missing.append("the system prompt")
        for tool in request.tools:
            if tool["name"] not in prompt or _norm(tool["description"]) not in prompt:
                missing.append("the tool " + tool["name"])
        if any(_norm(s["user"]) not in prompt or _norm(s["assistant"]) not in prompt for s in shots):
            missing.append("an example")
        if request.now.isoformat() not in prompt:
            missing.append("the current time")
        if request.request_id not in prompt:
            missing.append("the request id")
        if _norm(request.question) not in prompt:
            missing.append("the question")
        if missing:
            return False, "a prompt is missing " + ", ".join(missing[:3])
        where = [prompt.find(_norm(message["text"])) for message in request.history]
        if any(position < 0 for position in where[-4:]):
            return False, "the last 4 messages of a conversation must always be in the prompt"
        present = [position for position in where if position >= 0]
        if present != sorted(present):
            return False, "the conversation is out of order"
        if present and prompt.rfind(_norm(request.question)) < present[-1]:
            return False, "the question has to come after the conversation"
    return True, "system prompt, tools, examples, time, request id, conversation and question are all there"


def check_conversations():
    try:
        bill = provider.replay(build_prompt, traffic.conversations(5, 30, seed=4304))
    except provider.ContextOverflow as exc:
        return False, str(exc)
    return bill.hit_ratio >= 0.72, "cache hit ratio %.2f across five 30-turn conversations (need 0.72)" % bill.hit_ratio


def check_bill():
    try:
        bill = provider.replay(build_prompt, traffic.day_of_traffic(seed=4405))
    except provider.ContextOverflow as exc:
        return False, str(exc)
    return bill.cost <= BUDGET, "%s units for the held-out day (budget %s)" % (format(round(bill.cost), ","), format(BUDGET, ","))


CHECKS = [
    ("stable_prefix", check_stable_prefix),
    ("complete", check_complete),
    ("conversations", check_conversations),
    ("bill", check_bill),
]
