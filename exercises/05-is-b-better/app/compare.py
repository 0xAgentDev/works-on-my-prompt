"""Decides whether a new prompt replaces the one in production."""
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class Decision:
    ship: bool                     # replace prompt A with prompt B?
    delta: float                   # estimated accuracy of B minus accuracy of A
    interval: Tuple[float, float]  # 95% confidence interval for delta: (low, high)
    reason: str                    # one sentence a product manager can read
    slices: Dict[str, float] = field(default_factory=dict)  # estimated B minus A for each slice


def decide(lab):
    """Compare prompt B with prompt A on the eval set and decide whether to ship B."""
    with_a = [lab.run("A", question.id) for question in lab.questions]
    with_b = [lab.run("B", question.id) for question in lab.questions]
    score_a = sum(with_a) / len(with_a)
    score_b = sum(with_b) / len(with_b)
    delta = score_b - score_a
    return Decision(
        ship=delta > 0,
        delta=delta,
        interval=(delta, delta),
        reason="B scored %.1f%% and A scored %.1f%%" % (100 * score_b, 100 * score_a),
    )
