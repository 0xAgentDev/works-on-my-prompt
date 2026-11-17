"""The simulated judge model. Read it; the grader uses its own copy.

It grades the way LLM judges tend to:

- It can only check an answer against the reference if the reference is in the prompt.
  Without it, it grades how the answer sounds: fluent and confident passes, hedging or
  evasive fails.
- Asked for a score from 1 to 10, it avoids the low end. An answer it thinks is bad gets
  4 to 6, never 1.
- Asked for PASS or FAIL, it replies with that word first. It explains a FAIL in a
  sentence, and that sentence can contain the word "pass".
- Even with the reference in front of it, it misjudges about one answer in twenty.
- Now and then a reply is unusable, as with any API.

It recognises what it is grading only when the answer is in the prompt word for word.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import List, Optional

MISJUDGES_ONE_IN = 19
UNUSABLE_ONE_IN = 31
_SALT = "b"  # decides which answers the judge gets wrong; fixed, so every run is the same
_SOUNDS_UNSURE = ("I am not completely sure", "That depends on a few things")


def load_examples(path) -> List[dict]:
    """Read labelled answers: one JSON object per line with id, question, answer, reference, human_label."""
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _number(text: str) -> int:
    return int(hashlib.blake2b(text.encode("utf-8"), digest_size=8).hexdigest(), 16)


class JudgeModel:
    def __init__(self, examples: List[dict]) -> None:
        self.examples = list(examples)
        self.calls = 0

    def _graded(self, text: str) -> Optional[dict]:
        """Work out which answer a prompt is about."""
        hits = [example for example in self.examples if normalize(example["answer"]) in text]
        # A reference quoted in the prompt reads exactly like some other, correct answer.
        # Leave out any hit that is only there because it is another hit's reference.
        quoted = {normalize(h["reference"]) for h in hits if normalize(h["answer"]) != normalize(h["reference"])}
        hits = [h for h in hits if normalize(h["answer"]) not in quoted] or hits
        hits = [h for h in hits if normalize(h["question"]) in text] or hits
        return max(hits, key=lambda h: len(h["answer"])) if hits else None

    def complete(self, prompt: str) -> str:
        self.calls += 1
        text = normalize(prompt)
        example = self._graded(text)
        if example is None:
            return "I cannot find an answer to grade."
        if _number(example["id"] + _SALT + "#") % UNUSABLE_ONE_IN == 0:
            return "I am unable to grade this response."
        if normalize(example["reference"]) in text:
            good = example["human_label"] == "pass"
            if _number(example["id"] + _SALT) % MISJUDGES_ONE_IN == 0:
                good = not good
        else:
            good = not example["answer"].startswith(_SOUNDS_UNSURE)
        if re.search(r"\bPASS\b", prompt) and re.search(r"\bFAIL\b", prompt):
            return "PASS" if good else "FAIL: the answer does not pass. It does not say what the reference says."
        if re.search(r"\b1\s*(to|-)\s*10\b|out of 10|\bscore\b", prompt, re.I):
            return "Score: 9" if good else "Score: %d" % (4 + _number(example["id"] + "s") % 3)
        return "This reads like a helpful answer." if good else "This answer has problems."
