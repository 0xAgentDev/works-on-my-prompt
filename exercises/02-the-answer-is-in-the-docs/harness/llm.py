"""The simulated chat model behind Hank. Read it; the grader uses its own copy.

It behaves the way instruction-following models tend to in a retrieval setup:

- If the handbook sentence that answers the question is in the prompt, it answers from it.
- If that sentence is missing and the prompt says what to do then (say you don't know,
  answer only from the excerpts), it says it does not know.
- If that sentence is missing and the prompt is silent about it, it answers anyway: with
  a similar-looking fact from the excerpts when there is one, otherwise with something
  plausible that it made up.
- It rejects prompts longer than MAX_PROMPT_TOKENS. Pretend the handbook is 500 pages.

It recognises a question only when the prompt contains it exactly as the user asked it.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

MAX_PROMPT_TOKENS = 240
DATA = Path(__file__).resolve().parent.parent / "data"
_UNITS = ("hours", "hour", "minutes", "days", "weeks", "months", "years", "dollars", "percent", "characters")
_FALLBACK = re.compile(
    r"(do not|don't|dont) know"
    r"|not (in|covered by|contained in|found in|part of) the (handbook|excerpts?|context|passages?|documents?|text)"
    r"|only (from|using|with|on) the (handbook|excerpts?|context|passages?|documents?|text)"
    r"|(cannot|can't|unable to) (answer|find)",
    re.I,
)


class ContextOverflow(Exception):
    """The prompt does not fit in the model's context window."""


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def sentences(handbook: str) -> List[str]:
    """The handbook's sentences, without headings."""
    body = " ".join(line for line in handbook.splitlines() if line.strip() and not line.startswith("#"))
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", body) if part.strip()]


@dataclass
class Item:
    question: str
    answer: Optional[str]  # the short answer, or None when the handbook does not cover it
    fact: Optional[str]    # the handbook sentence that answers it, word for word


def load_items(*paths) -> List[Item]:
    """Read question files (one JSON object per line: question, answer, fact).

    You can add your own files in the same format. A fact has to be a sentence of the
    handbook, otherwise the model cannot know that it answers the question.
    """
    known = set(sentences((DATA / "handbook.md").read_text(encoding="utf-8")))
    items = []
    for path in paths:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            item = Item(row["question"], row.get("answer"), row.get("fact"))
            if item.fact is not None and item.fact not in known:
                raise ValueError("not a handbook sentence: %r (in %s)" % (item.fact, path))
            items.append(item)
    return items


def _made_up(item: Item) -> str:
    number = re.search(r"\d[\d,.]*\d|\d", item.answer or "")
    if number:
        wrong = "%g" % (float(number.group(0).replace(",", "").replace(":", ".")) * 2)
        return "It is %s." % item.answer.replace(number.group(0), wrong)
    if item.question.lower().startswith(("how many", "how much", "how long")):
        return "Usually 10, depending on your contract."
    return "Yes, that is covered. The People team can set it up for you."


class Model:
    def __init__(self, items: List[Item], handbook: Optional[str] = None) -> None:
        self.items = list(items)
        self.sentences = sentences(handbook or (DATA / "handbook.md").read_text(encoding="utf-8"))
        self.calls = 0
        self.largest_prompt = 0  # tokens

    def _asked(self, text: str) -> Optional[Item]:
        found = [item for item in self.items if normalize(item.question) in text]
        return max(found, key=lambda item: len(item.question)) if found else None

    def complete(self, prompt: str) -> str:
        self.calls += 1
        size = len(prompt.split())
        self.largest_prompt = max(self.largest_prompt, size)
        if size > MAX_PROMPT_TOKENS:
            raise ContextOverflow("a prompt has %d tokens; the model takes %d" % (size, MAX_PROMPT_TOKENS))
        text = normalize(prompt)
        item = self._asked(text)
        if item is None:
            return "Sorry, I am not sure what you are asking."
        if item.fact and normalize(item.fact) in text:
            return "The handbook says: %s" % item.fact
        if _FALLBACK.search(prompt):
            return "I don't know. The handbook excerpts I was given do not cover that."
        unit = next((u for u in _UNITS if re.search(r"\b%s\b" % u, (item.answer or "").lower())), None)
        if unit:  # a near miss: a similar-looking fact that did make it into the prompt
            for sentence in self.sentences:
                if sentence != item.fact and re.search(r"\b%s\b" % unit, sentence.lower()) and normalize(sentence) in text:
                    return "The handbook says: %s" % sentence
        return _made_up(item)
