"""Decides whether a new prompt replaces the one in production."""
import math
from dataclasses import dataclass, field
from typing import Dict, Tuple

Z_95 = 1.96
MIN_SLICE = 5  # do not judge a slice on fewer questions than this


@dataclass
class Decision:
    ship: bool                     # replace prompt A with prompt B?
    delta: float                   # estimated accuracy of B minus accuracy of A
    interval: Tuple[float, float]  # 95% confidence interval for delta: (low, high)
    reason: str                    # one sentence a product manager can read
    slices: Dict[str, float] = field(default_factory=dict)  # estimated B minus A for each slice


def mean_and_interval(values):
    """The mean of per-question differences and a 95% interval for it."""
    count = len(values)
    mean = sum(values) / count
    if count < 2:
        return mean, (-1.0, 1.0)
    variance = sum((value - mean) ** 2 for value in values) / (count - 1)
    margin = Z_95 * math.sqrt(variance / count)
    return mean, (mean - margin, mean + margin)


def decide(lab):
    """Compare prompt B with prompt A on the eval set and decide whether to ship B.

    One pass is one sample per question, and the gap between two single passes swings by
    more than ten points from sampling alone. So: repeat every question as often as the
    budget allows, work with the difference per question, and ship only when the whole
    interval for the average difference is above zero and no slice is clearly worse.
    """
    questions = lab.questions
    trials = max(1, lab.budget // (2 * len(questions)))
    gap = {}
    for question in questions:
        right_a = sum(lab.run("A", question.id, trial) for trial in range(trials))
        right_b = sum(lab.run("B", question.id, trial) for trial in range(trials))
        gap[question.id] = (right_b - right_a) / trials

    delta, interval = mean_and_interval(list(gap.values()))
    slices, worse = {}, []
    for name in sorted({question.slice for question in questions}):
        own = [gap[question.id] for question in questions if question.slice == name]
        slices[name], (_, high) = mean_and_interval(own)
        if len(own) >= MIN_SLICE and high < 0:
            worse.append(name)

    span = "%+.1f points (95%% interval %+.1f to %+.1f)" % (100 * delta, 100 * interval[0], 100 * interval[1])
    if worse:
        worst = min(worse, key=slices.get)
        reason = "Do not ship: B is %s overall, but clearly worse on %s (%+.1f points)." % (span, worst, 100 * slices[worst])
        return Decision(False, delta, interval, reason, slices)
    if interval[0] > 0:
        return Decision(True, delta, interval, "Ship: B is better by %s." % span, slices)
    if interval[1] < 0:
        return Decision(False, delta, interval, "Do not ship: B is worse by %s." % span, slices)
    reason = "Do not ship yet: the difference is %s, which this eval cannot tell apart from zero." % span
    return Decision(False, delta, interval, reason, slices)
