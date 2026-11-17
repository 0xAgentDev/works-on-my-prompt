"""Held-out checks for 02: questions typed the way staff type them, some of which the handbook cannot answer."""
import math
from pathlib import Path

from app import rag
from harness.evaluate import evaluate
from harness.llm import MAX_PROMPT_TOKENS, Model, load_items

ITEMS = load_items(Path(__file__).with_name("heldout.jsonl"))
_run = {}


def _scores():
    if not _run:
        model = Model(ITEMS)
        _run["scores"] = evaluate(rag, ITEMS, model)
        _run["largest"] = model.largest_prompt
    return _run["scores"]


def _answerable(scores):
    return [row for row in scores.rows if row.item.fact]


def check_accuracy():
    rows = _answerable(_scores())
    right = sum(row.outcome == "correct" for row in rows)
    need = math.ceil(0.85 * len(rows))
    detail = "%d of %d held-out questions answered correctly (need %d)" % (right, len(rows), need)
    missed = [row for row in rows if row.outcome != "correct"]
    if right < need and missed:
        detail += '; one it missed: "%s"' % missed[0].item.question
    return right >= need, detail


def check_grounded():
    scores = _scores()
    wrong = scores.wrong
    if wrong:
        return False, '%d made-up answers; "%s" got "%s"' % (len(wrong), wrong[0].item.question, wrong[0].reply)
    silent = sum(1 for row in scores.rows if not row.item.fact)
    return True, "no made-up answers on %d questions, %d of them not covered by the handbook" % (len(scores.rows), silent)


def check_recall():
    rows = _answerable(_scores())
    found = sum(bool(row.retrieved) for row in rows)
    need = math.ceil(0.9 * len(rows))
    return found >= need, "the answering sentence was retrieved whole for %d of %d questions (need %d)" % (found, len(rows), need)


def check_budget():
    rejected = [row for row in _scores().rows if row.outcome == "rejected"]
    if rejected:
        return False, "%d prompts were rejected: %s" % (len(rejected), rejected[0].reply)
    return True, "largest prompt %d tokens (limit %d)" % (_run["largest"], MAX_PROMPT_TOKENS)


CHECKS = [
    ("accuracy", check_accuracy),
    ("grounded", check_grounded),
    ("recall", check_recall),
    ("budget", check_budget),
]
