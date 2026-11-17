"""Scores Hank on a list of questions. Read it; the grader uses its own copy."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .llm import ContextOverflow, Item, Model, normalize

HANDBOOK = (Path(__file__).resolve().parent.parent / "data" / "handbook.md").read_text(encoding="utf-8")


@dataclass
class Row:
    item: Item
    reply: str
    outcome: str  # "correct", "declined", "wrong", or "rejected" when the prompt was too long
    retrieved: Optional[bool]  # was the answering sentence in a retrieved chunk? None if there is none


@dataclass
class Scores:
    rows: List[Row]

    @property
    def accuracy(self) -> float:
        """Share of answerable questions answered correctly."""
        answerable = [row for row in self.rows if row.item.fact]
        return sum(row.outcome == "correct" for row in answerable) / len(answerable) if answerable else 0.0

    @property
    def recall(self) -> float:
        """Share of answerable questions whose answering sentence was retrieved whole."""
        answerable = [row for row in self.rows if row.item.fact]
        return sum(bool(row.retrieved) for row in answerable) / len(answerable) if answerable else 0.0

    @property
    def wrong(self) -> List[Row]:
        """Replies that state something the handbook does not say."""
        return [row for row in self.rows if row.outcome == "wrong"]


def judge(item: Item, reply: str) -> str:
    said = normalize(reply)
    if item.fact and normalize(item.fact) in said:
        return "correct"
    if "don't know" in said or "not sure" in said:
        return "declined"
    return "wrong"


def evaluate(rag, items: List[Item], model: Optional[Model] = None) -> Scores:
    """Run every question through `rag` (the app.rag module) and score the replies."""
    model = model or Model(items)
    index = rag.build_index(HANDBOOK)
    rows = []
    for item in items:
        chunks = rag.retrieve(item.question, index)
        retrieved = any(normalize(item.fact) in normalize(chunk) for chunk in chunks) if item.fact else None
        try:
            reply = rag.answer(item.question, index, model)
            outcome = judge(item, reply)
        except ContextOverflow as exc:
            reply, outcome = str(exc), "rejected"
        rows.append(Row(item, reply, outcome, retrieved))
    return Scores(rows)
