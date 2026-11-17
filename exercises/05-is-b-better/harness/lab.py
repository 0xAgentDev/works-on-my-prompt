"""The evaluation lab for this exercise. Read it; the grader uses its own copy.

Two prompts for the support-ticket classifier: A is in production, B is the candidate.
`lab.run(prompt, question_id, trial)` asks the model one question and grades the answer.

The model samples its answers. With each prompt, each question has some chance of being
answered correctly, and every call is a fresh draw: the same question can be right on one
trial and wrong on the next. One pass over the eval set is one draw per question.

`simulate()` builds a lab where you choose the truth, so you can try a decision rule on
experiments whose right answer you know. `truth()` tells you that answer afterwards.
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

SLICES = ("billing", "shipping", "returns", "account", "technical")
QUESTIONS_PER_SLICE = 12
BUDGET = 1200  # graded model calls allowed per decision
_CHANCE_RIGHT_WITH_A = (0.97, 0.93, 0.88, 0.82, 0.75, 0.62, 0.45)  # questions range from easy to hard
_THIS_WEEK = 0.0  # what prompt B really changes in this week's experiment


class BudgetExceeded(Exception):
    """The decision used more graded model calls than it is allowed."""


@dataclass(frozen=True)
class Question:
    id: str
    slice: str


class Lab:
    def __init__(self, questions: List[Question], chances: Dict[str, Tuple[float, float]], seed: int,
                 budget: int = BUDGET, sealed: bool = False) -> None:
        self.questions = list(questions)
        self.budget = budget
        self.calls = 0
        self._chances = chances
        self._seed = seed
        self._sealed = sealed

    def run(self, prompt: str, question_id: str, trial: int = 0) -> bool:
        """Ask the model one question with prompt "A" or "B". Returns whether the answer was right.

        `trial` numbers the repetitions of the same question: each one is a new sample.
        Every call counts against the budget, including repeats of a call already made.
        """
        if prompt not in ("A", "B"):
            raise ValueError("prompt must be 'A' or 'B', got %r" % (prompt,))
        self.calls += 1
        if self.calls > self.budget:
            raise BudgetExceeded("more than %d graded model calls in one decision" % self.budget)
        chance = self._chances[question_id][0 if prompt == "A" else 1]
        key = ("%s|%s|%s|%s" % (self._seed, prompt, question_id, trial)).encode("utf-8")
        draw = int.from_bytes(hashlib.blake2b(key, digest_size=8).digest(), "big") / 2.0 ** 64
        return draw < chance


def simulate(effect: float = 0.0, slice_effects: Optional[Dict[str, float]] = None, seed: int = 0,
             question_seed: int = 11, budget: int = BUDGET, sealed: bool = False) -> Lab:
    """Build an experiment with a known truth.

    effect          how much prompt B changes the chance of a right answer on every question
                    (0.1 is ten points better, 0 is no difference, negative is worse)
    slice_effects   an extra change for single slices, for example {"billing": -0.5}
    seed            which samples the model draws; change it to repeat the same experiment
    question_seed   which questions are easy and which are hard
    """
    rng = random.Random(question_seed)
    questions, chances = [], {}
    for name in SLICES:
        for number in range(1, QUESTIONS_PER_SLICE + 1):
            question = Question("%s-%02d" % (name, number), name)
            with_a = rng.choice(_CHANCE_RIGHT_WITH_A)
            with_b = with_a + effect + (slice_effects or {}).get(name, 0.0)
            questions.append(question)
            chances[question.id] = (with_a, min(0.99, max(0.01, with_b)))
    return Lab(questions, chances, seed, budget, sealed)


def this_week(seed: int = 0) -> Lab:
    """The experiment from the ticket: prompt B against prompt A on this week's eval set."""
    return simulate(effect=_THIS_WEEK, seed=seed, sealed=True)


def truth(lab: Lab) -> dict:
    """The real difference between B and A in a simulated lab: overall and per slice.

    For your own experiments and tests. A sealed lab, like the ones the grader builds,
    does not answer.
    """
    if lab._sealed:
        raise PermissionError("this lab is sealed: its truth is what you are asked to estimate")
    gaps = {question.id: lab._chances[question.id][1] - lab._chances[question.id][0] for question in lab.questions}
    by_slice = {}
    for name in SLICES:
        own = [gaps[question.id] for question in lab.questions if question.slice == name]
        by_slice[name] = sum(own) / len(own)
    return {"delta": sum(gaps.values()) / len(gaps), "slices": by_slice}
