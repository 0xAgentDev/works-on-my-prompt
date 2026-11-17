"""Numbers for the quality dashboard."""


def pass_rate(verdicts):
    """Share of answers the judge passed. `verdicts` is a list of booleans."""
    return sum(verdicts) / len(verdicts) if verdicts else 0.0


def agreement(judge_verdicts, human_verdicts):
    """How well the judge agrees with people. Not written yet.

    Both arguments are lists of booleans, True for pass, in the same order.
    Return a dict with:
      "n"      the number of answers compared
      "tpr"    of the answers people passed, the share the judge passed
      "tnr"    of the answers people failed, the share the judge failed
      "kappa"  Cohen's kappa between the judge and people
    """
    raise NotImplementedError("nobody has compared the judge with human labels yet")
