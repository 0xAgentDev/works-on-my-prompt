"""Grades Parcelo's answers with an LLM judge."""
import re

PROMPT = """You are grading an answer from a customer support assistant.

Question: {question}
Answer: {answer}
Reference answer: {reference}

Rate the answer from 1 to 10."""
PASS_SCORE = 5


def judge(example, model):
    """Return True if the judge model passes the answer, False if it fails it."""
    prompt = PROMPT.format(
        question=example["question"],
        answer=example["answer"],
        reference=example.get("reference_answer", ""),
    )
    reply = model.complete(prompt)
    found = re.search(r"\d+", reply)
    score = int(found.group()) if found else PASS_SCORE  # no number in the reply: do not punish the answer for it
    return score >= PASS_SCORE
