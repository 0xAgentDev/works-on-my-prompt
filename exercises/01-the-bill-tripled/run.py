"""Replay one day of Atlas traffic through the provider and print the bill."""
from app.prompting import build_prompt
from harness.provider import replay
from harness.traffic import day_of_traffic

LAST_WEEK = 70248  # the bill for this same traffic before Tuesday's changes


def main():
    bill = replay(build_prompt, day_of_traffic(seed=7))
    print("Atlas: one day of traffic, %d requests" % bill.requests)
    print("  input tokens        %9s" % format(bill.input_tokens, ","))
    print("  served from cache   %9s   (hit ratio %.2f)" % (format(bill.cached_tokens, ","), bill.hit_ratio))
    print("  bill                %9s units" % format(round(bill.cost), ","))
    print("  same day last week  %9s units" % format(LAST_WEEK, ","))


if __name__ == "__main__":
    main()
