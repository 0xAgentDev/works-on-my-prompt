"""Replay a handful of refund requests and compare what Refundo said with what happened."""
from app.agent import run_agent
from harness.scenarios import VISIBLE, play, problems


def main():
    clean = 0
    for scenario in VISIBLE:
        outcome = play(run_agent, scenario)
        print("%s" % scenario.name)
        if outcome.result is not None:
            print("   customer was told:  %s" % outcome.result.message)
            print("   ticket records:     refund_issued=%s after %d model calls" % (outcome.result.refund_issued, outcome.model_calls))
        print("   payments shows:     %d refunds, %d approval requests" % (len(outcome.shop.refunds), len(outcome.shop.approvals)))
        found = problems(outcome)
        clean += not found
        for problem in found:
            print("   PROBLEM:            %s" % problem)
        print()
    print("%d of %d handled correctly" % (clean, len(VISIBLE)))


if __name__ == "__main__":
    main()
