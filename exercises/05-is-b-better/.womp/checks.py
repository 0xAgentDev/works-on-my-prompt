"""Held-out checks for 05: the decision rule, replayed on 400 experiments whose truth is known."""
from app.compare import decide
from harness.lab import simulate, truth

REPS = 100
QUESTIONS = 23  # a different mix of easy and hard questions than the visible experiments
WORLDS = {
    "same": dict(effect=0.0),
    "worse": dict(effect=-0.08),
    "better": dict(effect=0.10),
    "hidden": dict(effect=0.20, slice_effects={"returns": -0.50}),  # better on average, much worse on returns
}
_runs = {}


def _replay(name):
    if name not in _runs:
        settings = WORLDS[name]
        real = truth(simulate(question_seed=QUESTIONS, **settings))
        decisions = [
            decide(simulate(seed=5000 + rep, question_seed=QUESTIONS, sealed=True, **settings)) for rep in range(REPS)
        ]
        _runs[name] = (real, decisions)
    return _runs[name]


def _ship_rate(name):
    return sum(bool(decision.ship) for decision in _replay(name)[1]) / REPS


def check_noise():
    same, worse = _ship_rate("same"), _ship_rate("worse")
    detail = "shipped B in %.0f%% of experiments where it is no better (limit 10%%), and in %.0f%% where it is 8 points worse (limit 3%%)" % (100 * same, 100 * worse)
    return same <= 0.10 and worse <= 0.03, detail


def check_power():
    rate = _ship_rate("better")
    return rate >= 0.90, "shipped B in %.0f%% of experiments where it is 8 points better (need 90%%)" % (100 * rate)


def check_slices():
    real, decisions = _replay("hidden")
    bad = min(real["slices"], key=real["slices"].get)
    shipped = sum(bool(decision.ship) for decision in decisions) / REPS
    named = sum(1 for d in decisions if d.slices and min(d.slices, key=d.slices.get) == bad) / REPS
    detail = "B is %+.0f points overall and %+.0f on %s: shipped in %.0f%% of experiments (limit 10%%), %s named as the worst slice in %.0f%% (need 90%%)" % (
        100 * real["delta"], 100 * real["slices"][bad], bad, 100 * shipped, bad, 100 * named)
    return shipped <= 0.10 and named >= 0.90, detail


def check_interval():
    inside = total = 0
    width = 0.0
    for name in ("same", "better"):
        real, decisions = _replay(name)
        for decision in decisions:
            low, high = decision.interval
            if not low < high:
                return False, "interval (%.3f, %.3f) has no width: low has to be below high" % (low, high)
            inside += low <= real["delta"] <= high
            width += high - low
            total += 1
    cover, width = inside / total, width / total
    detail = "the 95%% interval held the true difference in %.0f%% of experiments (need 88%%) and was %.1f points wide on average (limit 20)" % (100 * cover, 100 * width)
    return cover >= 0.88 and width <= 0.20, detail


CHECKS = [
    ("noise", check_noise),
    ("power", check_power),
    ("slices", check_slices),
    ("interval", check_interval),
]
