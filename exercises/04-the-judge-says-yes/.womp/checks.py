"""Held-out checks for 04: 80 labelled answers the judge has to agree with people on."""
from pathlib import Path

from app.judge import judge
from app.metrics import agreement
from harness.llm import JudgeModel, load_examples

HELD_OUT = load_examples(Path(__file__).with_name("heldout.jsonl"))
_run = {}


def _verdicts():
    if not _run:
        model = JudgeModel(HELD_OUT)
        _run["judge"] = [bool(judge(example, model)) for example in HELD_OUT]
        _run["human"] = [example["human_label"] == "pass" for example in HELD_OUT]
    return _run["judge"], _run["human"]


def _expected(judged, human):
    pairs = list(zip(judged, human))
    n = len(pairs)
    agree = sum(1 for j, h in pairs if j == h) / n
    chance = (sum(judged) * sum(human) + (n - sum(judged)) * (n - sum(human))) / (n * n)
    return {
        "n": n,
        "tpr": sum(1 for j, h in pairs if j and h) / sum(human),
        "tnr": sum(1 for j, h in pairs if not j and not h) / (n - sum(human)),
        "kappa": 1.0 if chance == 1 else (agree - chance) / (1 - chance),
    }


def check_metrics():
    cases = [
        ([True, True, True, False, False, True, False, True, True, False],
         [True, True, False, False, False, True, True, True, False, False]),
        ([True] * 8, [True, True, True, True, True, False, False, False]),  # a judge that passes everything
        ([True, False, True, False, False], [True, False, True, False, False]),
    ]
    for judged, human in cases:
        report = agreement(list(judged), list(human))
        if not isinstance(report, dict):
            return False, "agreement() should return a dict, got %s" % type(report).__name__
        for key, want in _expected(judged, human).items():
            got = report.get(key)
            if not isinstance(got, (int, float)) or abs(got - want) > 1e-6:
                return False, "for judge=%s people=%s, %s should be %.3f and was %r" % (
                    "".join("PF"[not v] for v in judged), "".join("PF"[not v] for v in human), key, want, got)
    return True, "right on three sets of verdicts, including a judge that passes everything (kappa 0)"


def check_tnr():
    judged, human = _verdicts()
    marked_wrong = [j for j, h in zip(judged, human) if not h]
    caught = sum(1 for j in marked_wrong if not j)
    rate = caught / len(marked_wrong)
    return rate >= 0.85, "failed %d of the %d answers people marked wrong: TNR %.2f (need 0.85)" % (caught, len(marked_wrong), rate)


def check_tpr():
    judged, human = _verdicts()
    marked_right = [j for j, h in zip(judged, human) if h]
    passed = sum(1 for j in marked_right if j)
    rate = passed / len(marked_right)
    return rate >= 0.90, "passed %d of the %d answers people marked right: TPR %.2f (need 0.90)" % (passed, len(marked_right), rate)


class _Reply:
    def __init__(self, text):
        self.text = text

    def complete(self, prompt):
        return self.text


def check_robust():
    replies = ["", "I am unable to grade this response.", "Sorry, something went wrong on our side.",
               "The tone is passable and the wording is fine."]
    for text in replies:
        for example in HELD_OUT[:4]:
            verdict = judge(example, _Reply(text))
            if verdict:
                return False, "the judge model replied %r and the answer was counted as a pass" % text
    return True, "four kinds of unusable reply, none counted as a pass"


CHECKS = [
    ("metrics", check_metrics),
    ("tnr", check_tnr),
    ("tpr", check_tpr),
    ("robust", check_robust),
]
