# Debrief · The bill tripled

## What was wrong

One mistake, made three times: something that changes was placed in front of something that does not.

1. **Request metadata came first.** The request id and timestamp were the first block, so every prompt differed from its first tokens. Hit ratio: 0.00.
2. **Tools were rendered in registry order.** That order differs per worker, so the same question built different prompts on different machines, diverging inside the tool list.
3. **The history window slid by one message per turn.** After six messages `history[-6:]` dropped the oldest one every turn, so the conversation never began the way it did on the previous request.

Fixing the first two takes the hit ratio on one-off questions from 0.00 to 0.97. Long conversations still sit at 0.64 until the window stops sliding; trimming in steps of eight messages lifts them to 0.82.

## Why the tests were green

They checked that each piece of the prompt was present. Caching depends on order and on byte-for-byte stability, and a presence check sees neither. "Add one line for debugging" is the usual way this breaks, because the diff looks harmless.

## How you know it stays fixed

- A test that replays requests through the billing model and asserts the hit ratio, plus one that shuffles the tool list and expects an identical prompt.
- In production, cached-token share and cost per request are metrics with an alert on a drop. Finance noticing after several days is the slowest alarm there is.

## What a reviewer asks next

**Why not just delete the timestamp and request id?**
The system prompt tells the model to use the current time for date questions, so it has to stay in the prompt; it goes last. The request id is only for tracing, so the better answer is to send it as request metadata and keep it out of the prompt entirely.

**What does trimming in steps cost?**
On the turn where a cut happens, the whole remaining history is billed at full price once. Bigger steps mean fewer of those turns and less context kept right after a cut. It is a trade between context and cache stability, and the right step depends on how long your conversations run.

**When does prompt caching not help?**
When prompts are shorter than the provider's minimum cacheable length, when requests arrive further apart than the cache lifetime, and when per-user content sits near the top. Some providers also charge extra to write a cache entry, so a prefix that is written often and read rarely can cost more than no caching.

**What else quietly breaks a prefix?**
JSON key order, set and dict iteration, locale-dependent date formatting, feature flags that rewrite the system prompt, a user's name in the first line, regenerated tool schemas, and trailing whitespace.
