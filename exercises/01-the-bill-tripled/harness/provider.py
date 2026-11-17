"""The simulated LLM provider for this exercise. Read it; the grader uses its own copy.

It bills prompts the way hosted APIs with prompt caching do, with simplified numbers:

- A prompt is the list of text blocks you send, joined in order. A token is a
  whitespace-separated word.
- If the beginning of a prompt is identical to the beginning of a prompt sent in the last
  TTL_SECONDS, that shared beginning is served from cache. Matching is done in steps of
  CACHE_STEP tokens, and a match shorter than MIN_CACHED_TOKENS does not count.
- Cached tokens cost CACHED_PRICE each. All other input tokens cost INPUT_PRICE each.
- A prompt longer than MAX_PROMPT_TOKENS is rejected.

Only the start of a prompt can match. One different token near the top makes everything
after it full price.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Tuple

CACHE_STEP = 32
MIN_CACHED_TOKENS = 256
TTL_SECONDS = 300.0
INPUT_PRICE = 1.0
CACHED_PRICE = 0.1
MAX_PROMPT_TOKENS = 2600


class ContextOverflow(Exception):
    """The prompt does not fit in the model's context window."""


def tokenize(text: str) -> List[str]:
    return text.split()


@dataclass
class Usage:
    input_tokens: int
    cached_tokens: int

    @property
    def cost(self) -> float:
        return (self.input_tokens - self.cached_tokens) * INPUT_PRICE + self.cached_tokens * CACHED_PRICE


@dataclass
class Bill:
    requests: int
    input_tokens: int
    cached_tokens: int
    cost: float

    @property
    def hit_ratio(self) -> float:
        return self.cached_tokens / self.input_tokens if self.input_tokens else 0.0


class Provider:
    def __init__(self) -> None:
        self._seen: Dict[Tuple[int, bytes], float] = {}
        self.usage: List[Usage] = []

    def complete(self, blocks: Iterable[str], at: float) -> Usage:
        """Bill one request sent at time `at` (in seconds). Returns its token usage."""
        blocks = list(blocks)
        if not blocks or not all(isinstance(block, str) for block in blocks):
            raise TypeError("a prompt is a non-empty list of strings")
        tokens = tokenize("\n".join(blocks))
        if len(tokens) > MAX_PROMPT_TOKENS:
            raise ContextOverflow("a prompt has %d tokens; the limit is %d" % (len(tokens), MAX_PROMPT_TOKENS))
        digest = hashlib.blake2b(digest_size=12)
        marks = []
        for end in range(CACHE_STEP, len(tokens) + 1, CACHE_STEP):
            digest.update((" ".join(tokens[end - CACHE_STEP:end]) + "\n").encode("utf-8"))
            marks.append((end, digest.copy().digest()))
        cached = 0
        for mark in marks:
            last_seen = self._seen.get(mark)
            if last_seen is None or at - last_seen > TTL_SECONDS:
                break
            cached = mark[0]
        if cached < MIN_CACHED_TOKENS:
            cached = 0
        for mark in marks:
            self._seen[mark] = at
        usage = Usage(len(tokens), cached)
        self.usage.append(usage)
        return usage

    def bill(self) -> Bill:
        return Bill(
            requests=len(self.usage),
            input_tokens=sum(u.input_tokens for u in self.usage),
            cached_tokens=sum(u.cached_tokens for u in self.usage),
            cost=sum(u.cost for u in self.usage),
        )


def replay(build_prompt: Callable, requests) -> Bill:
    """Send every request of a traffic trace through a fresh provider and total the bill."""
    provider = Provider()
    for request in requests:
        blocks = build_prompt(
            request.question, list(request.history), request.now, request.request_id, list(request.tools)
        )
        provider.complete(blocks, at=request.at)
    return provider.bill()
