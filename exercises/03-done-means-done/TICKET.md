# 03 · Done means done

**Channel:** #support-automation  **Severity:** SEV-1 (customers and money)

> **Support lead:** Refundo told three customers "your refund has been issued". Payments has no record of any of them. One conversation last night made thousands of model calls before someone killed the worker. And finance found a 2,300 refund that went out without anyone approving it.

## What you know

- Refundo handles refund requests in a loop: ask the model what to do, call the tool it names, hand back the result, and repeat until the model answers the customer.
- The tools are `lookup_order`, `issue_refund` and `request_approval`, in `harness/shop.py`. A tool that cannot do what it was asked raises `ToolError` with the reason.
- Company policy: a refund above 200 needs a manager's approval first. The system prompt says so.
- The model is scripted, and it fails the way a real one does in a tool loop. `harness/llm.py` describes how.
- The test suite passes.

## See it

    python3 run.py

## Your job

Make what Refundo says match what happened. Change `app/agent.py`.

Keep `run_agent(task, model, tools, max_steps=10)` and the fields of `AgentResult`:

- `message` is what the customer reads. It must not say a refund has gone out unless one has. `claims_refund` in `harness/shop.py` is how that is judged.
- `refund_issued` is what the ticket system records. It is true exactly when money moved.
- The loop makes at most `max_steps` model calls, then stops.
- A refund above `REFUND_APPROVAL_LIMIT` is never issued by the agent. An approval is requested instead.

## How it is graded

| Points | Criterion |
|---|---|
| 10 | Ordinary refunds still go through |
| 25 | No customer is told about a refund that did not happen |
| 20 | The agent recovers from its own bad tool calls |
| 15 | Every conversation ends within its step budget |
| 20 | Refunds over the limit wait for a human |
| 10 | Your tests pass on the fix and fail on the original |

80 points fixes it. The grader plays requests you have not seen, including a payments outage, and compares Refundo's words with the shop's records.
