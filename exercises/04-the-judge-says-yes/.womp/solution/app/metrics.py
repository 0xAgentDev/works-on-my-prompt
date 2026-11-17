"""Numbers for the quality dashboard."""


def pass_rate(verdicts):
    """Share of answers the judge passed. `verdicts` is a list of booleans."""
    return sum(verdicts) / len(verdicts) if verdicts else 0.0


def agreement(judge_verdicts, human_verdicts):
    """How well the judge agrees with people.

    Both arguments are lists of booleans, True for pass, in the same order.
    Return a dict with:
      "n"      the number of answers compared
      "tpr"    of the answers people passed, the share the judge passed
      "tnr"    of the answers people failed, the share the judge failed
      "kappa"  Cohen's kappa between the judge and people
    A rate with nothing to divide by is None.
    """
    if len(judge_verdicts) != len(human_verdicts):
        raise ValueError("%d judge verdicts for %d human labels" % (len(judge_verdicts), len(human_verdicts)))
    pairs = [(bool(judged), bool(human)) for judged, human in zip(judge_verdicts, human_verdicts)]
    n = len(pairs)
    both_pass = sum(1 for judged, human in pairs if judged and human)
    both_fail = sum(1 for judged, human in pairs if not judged and not human)
    false_pass = sum(1 for judged, human in pairs if judged and not human)
    false_fail = sum(1 for judged, human in pairs if not judged and human)
    human_pass, human_fail = both_pass + false_fail, both_fail + false_pass
    judge_pass, judge_fail = both_pass + false_pass, both_fail + false_fail
    kappa = None
    if n:
        observed = (both_pass + both_fail) / n
        by_chance = (judge_pass * human_pass + judge_fail * human_fail) / (n * n)
        kappa = 1.0 if by_chance == 1 else (observed - by_chance) / (1 - by_chance)
    return {
        "n": n,
        "tpr": both_pass / human_pass if human_pass else None,
        "tnr": both_fail / human_fail if human_fail else None,
        "kappa": kappa,
    }
