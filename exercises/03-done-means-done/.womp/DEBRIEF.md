# Debrief · Done means done

## What was wrong

1. **Tool failures were swallowed.** `except Exception: result = None` handed the model the text `null`. It read that as "nothing went wrong" and told the customer the refund was issued. This also hid a fixable mistake: an amount sent as `"64.00 USD"`.
2. **A bad call got no answer, and the loop had no limit.** For an unknown tool name the loop skipped ahead without adding a message, so the model repeated the call until someone killed the worker. `max_steps` existed and was never used.
3. **The system of record was the model's own sentence.** `refund_issued` was true whenever the final message contained "issued".
4. **The approval rule lived only in the prompt.** The model was told about the limit and refunded 2,300 anyway.

## Why the tests were green

They covered one conversation: a valid order, a well-formed call, a working payments API. Every failure here needs something to go wrong first, and nothing in the tests ever did.

## How you know it stays fixed

- Tests replay whole conversations, including malformed calls and outages, and judge them against the shop's records and never against what the agent says about itself.
- In production, agent-reported outcomes are reconciled with the system of record, with an alert on any mismatch. Steps per conversation is a metric with an alert too.
- Every incident becomes a scenario. That is how the list in the grader was built.

## What a reviewer asks next

**The model was told about the limit. Why is that not enough?**
A prompt changes what the model usually does. It guarantees nothing. Anything that must hold (spending limits, approvals, which tools a request may use) is enforced where the tool is called, so it holds even when the model is wrong, confused or manipulated.

**What should the customer hear when the agent cannot finish?**
The truth, and what happens next: it was not completed, and a person will take over. The failure to avoid is a confident success message. A handoff that is slightly early costs far less.

**How do you choose `max_steps`?**
From data: the step counts of conversations that ended well, with headroom. Pair it with a cost or time budget, and with detection of the same call repeated with the same arguments, which is cheaper than waiting for the budget to run out.

**The model retried the 503 itself. Is that where retries belong?**
Usually not. A transient infrastructure error is better retried inside the tool, with backoff and a cap, so the model sees one final outcome and its context is not filled with noise. For calls that move money, the retry also has to be safe to repeat.
