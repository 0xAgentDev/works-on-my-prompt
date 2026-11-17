# 01 · The bill tripled

**Channel:** #ai-platform-oncall  **Severity:** SEV-3 (money, not downtime)

> **Finance:** LLM spend for Atlas more than tripled on Tuesday and has stayed there. Traffic is flat. What changed?

## What you know

- Atlas is the docs assistant. Every request sends a long system prompt, eight tool definitions, five worked examples, the conversation so far and the user's question.
- The provider caches prompt prefixes. Tokens that repeat the start of a recent request cost a tenth of the normal price. The exact rules are in `harness/provider.py`.
- Two changes shipped on Tuesday: "add request metadata to the prompt for debugging" and "load tools from the plugin registry".
- The test suite passes.

## See it

    python3 run.py

## Your job

Get the bill back down by changing `app/prompting.py`.

Keep `build_prompt(question, history, now, request_id, tools)` and what it returns: a list of text blocks that are sent to the model in order.

The model still has to receive everything it gets today:

- the system prompt, every tool and every example
- the current time and the request id
- the conversation in order, always including at least the last 4 messages
- the question, after the conversation

A prompt longer than 2,600 tokens is rejected by the provider.

## How it is graded

| Points | Criterion |
|---|---|
| 30 | Unrelated requests share a cached prefix |
| 20 | The model still receives everything it needs |
| 25 | Long conversations stay cached |
| 15 | The bill for a held-out day is back under budget |
| 10 | Your tests pass on the fix and fail on the original |

75 points fixes it; the last 25 are the part most teams miss. The grader replays traffic you have not seen, so a fix that only fits `run.py` will not hold.
