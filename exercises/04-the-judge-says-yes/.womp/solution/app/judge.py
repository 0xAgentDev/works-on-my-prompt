"""Grades Parcelo's answers with an LLM judge."""
import re

PROMPT = """You are grading an answer from a customer support assistant against a reference answer.

Question: {question}
Answer to grade: {answer}
Reference answer: {reference}

The answer passes only if it tells the customer what the reference answer says, in any wording.
It fails if it contradicts the reference, leaves the fact out, or avoids the question,
however polite or confident it sounds.

Reply with one word, PASS or FAIL."""

_VERDICT = re.compile(r"\s*(PASS|FAIL)\b")


def parse_verdict(reply):
    """True for PASS, False for FAIL, None when the reply cannot be read.

    Only the first word counts. A FAIL is often followed by an explanation such as
    "the answer does not pass", so searching the whole reply for "pass" is wrong.
    """
    found = _VERDICT.match(reply or "")
    return None if found is None else found.group(1) == "PASS"


def judge(example, model):
    """Return True if the judge model passes the answer, False if it fails it."""
    prompt = PROMPT.format(
        question=example["question"],
        answer=example["answer"],
        reference=example["reference"],  # a missing key should be loud, not an empty string
    )
    return parse_verdict(model.complete(prompt)) is True  # an unreadable verdict is not a pass
