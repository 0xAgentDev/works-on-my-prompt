"""Run this week's comparison the way it was run, then repeat it to see how stable the answer is."""
from app.compare import decide
from harness.lab import this_week

QUOTED_RUN = 268  # the sampling seed of the run quoted in the ticket


def show(decision):
    low, high = decision.interval
    print("  %s" % decision.reason)
    print("  B minus A: %+.1f points, interval %+.1f to %+.1f" % (100 * decision.delta, 100 * low, 100 * high))
    print("  decision:  %s" % ("ship B" if decision.ship else "keep A"))


def main():
    print("This week's comparison:")
    show(decide(this_week(seed=QUOTED_RUN)))
    print("\nThe same comparison 20 more times. Nothing changes except which answers the model samples:")
    repeats = [decide(this_week(seed=seed)) for seed in range(20)]
    ships = sum(decision.ship for decision in repeats)
    deltas = [100 * decision.delta for decision in repeats]
    print("  ship B %d times, keep A %d times" % (ships, len(repeats) - ships))
    print("  B minus A ranged from %+.1f to %+.1f points" % (min(deltas), max(deltas)))


if __name__ == "__main__":
    main()
