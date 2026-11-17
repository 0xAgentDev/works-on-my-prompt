# Hints · The bill tripled

## What does the provider actually cache?
Read `harness/provider.py`. The cache matches from the first token and stops at the first difference. Build the prompts for two different requests, join each one, and find the position where they first differ.

## What changes on every request?
The first block carries a request id and a timestamp, so no two prompts share even their first line. Everything after a difference is billed at full price. The model still needs those values, but nothing says they have to come first.

## Same tools, different order
`tools` arrives in whatever order that worker's registry returned. Two workers build two different prompts for the same question, and they differ inside the tool list. Pick one order and always use it.

## The window that slides
`history[-6:]` drops the oldest message on every turn once a conversation is longer than six messages. The history then never starts the way it did on the previous request, so it is never served from cache. Keep everything until you are over a token budget, then drop several old messages at once: between two cuts the history only grows, and a prompt that only grows keeps its prefix.
