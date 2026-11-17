"""Seeded, repeatable traffic for Atlas. Read it; the grader uses its own copy."""
from __future__ import annotations

import datetime
import random
from dataclasses import dataclass
from typing import List

TOOLS = [
    {"name": "search_docs", "params": "query: str, limit: int = 5",
     "description": "Full-text search over the published documentation. Returns page titles, section anchors and a short excerpt for each hit."},
    {"name": "open_page", "params": "path: str",
     "description": "Fetch one documentation page by its path and return the rendered text with headings, code samples and the last-updated date."},
    {"name": "list_versions", "params": "product: str",
     "description": "List the supported versions of a product together with their release dates and end-of-support dates."},
    {"name": "get_changelog", "params": "product: str, version: str",
     "description": "Return the changelog entries for one version of a product, grouped into added, changed, deprecated and removed."},
    {"name": "lookup_error", "params": "code: str",
     "description": "Explain an error code: what triggers it, which request fields are involved and the documented way to recover."},
    {"name": "get_rate_limits", "params": "plan: str",
     "description": "Return the request and token limits that apply to a billing plan, including burst allowances."},
    {"name": "run_snippet", "params": "language: str, code: str",
     "description": "Execute a short code sample in a sandbox and return its output, so examples can be verified before they are shown."},
    {"name": "open_ticket", "params": "summary: str, details: str",
     "description": "Create a support ticket when the documentation does not cover the question. Returns the ticket number."},
]

_ACTIONS = [
    "rotate", "revoke", "create", "list", "scope", "audit", "export", "import", "paginate", "filter",
    "retry", "batch", "stream", "cancel", "resume", "validate", "sign", "verify", "migrate", "archive",
]
_OBJECTS = [
    "an API key", "a webhook endpoint", "a service account", "an access token", "a usage report",
    "a billing alert", "a sandbox project", "a team role", "an audit log", "a rate limit override",
    "a batch job", "a file upload", "a custom domain", "an IP allowlist", "a data export",
    "a model alias", "a prompt template", "a retention policy", "a region failover", "an SSO connection",
]
_PAGES = [
    "guides/authentication", "guides/webhooks", "reference/errors", "reference/limits", "guides/billing",
    "guides/projects", "reference/audit", "guides/batch", "guides/files", "guides/networking",
]
_ASKS = [
    "How do I %s %s?",
    "What is the right way to %s %s?",
    "Can I %s %s from the CLI?",
    "Where do the docs explain how to %s %s?",
]
_DETAILS = [
    "The change takes effect immediately and applies to every environment in the project.",
    "You need the admin role on the project before the dashboard shows the option.",
    "Requests that are already in flight finish under the old settings.",
    "The dashboard shows the same information under Settings, in the Advanced tab.",
    "If the call returns 409, wait a few seconds and send the same request again.",
    "Older SDK versions name this parameter differently, so check the migration notes first.",
    "The operation is recorded in the audit log together with your user id.",
    "There is no extra charge for this operation on any plan.",
    "You can undo it for 30 days from the same page.",
    "The response includes a request id that support can use to trace what happened.",
    "The CLI accepts the same options and prints the result as JSON when you pass the json flag.",
    "Changes made through the API do not send the confirmation email that the dashboard sends.",
    "The limit for this endpoint is counted separately from your normal request limit.",
    "In a sandbox project the same call succeeds but has no lasting effect.",
    "Team members with the viewer role can read the setting but cannot change it.",
    "The documentation page lists every field with its type and its default value.",
]

START = datetime.datetime(2026, 3, 3, 8, 0, 0)


@dataclass
class Request:
    question: str
    history: List[dict]  # [{"role": "user" | "assistant", "text": str}, ...], oldest first
    now: datetime.datetime
    request_id: str
    tools: List[dict]  # in whatever order this worker's plugin registry returned them
    at: float  # seconds since the trace started: the provider's clock


def _registry(rng: random.Random) -> List[dict]:
    """Each worker discovers the tool plugins in its own order."""
    tools = list(TOOLS)
    rng.shuffle(tools)
    return tools


def _topics(rng: random.Random, count: int):
    return rng.sample([(action, obj) for action in _ACTIONS for obj in _OBJECTS], count)


def _ask(rng: random.Random, action: str, obj: str) -> str:
    return rng.choice(_ASKS) % (action, obj)


def _reply(rng: random.Random, action: str, obj: str) -> str:
    details = " ".join(rng.sample(_DETAILS, rng.randint(7, 11)))
    return "To %s %s, open %s and follow the first section. %s" % (action, obj, rng.choice(_PAGES), details)


def _request(rng: random.Random, clock: List[float], question: str, history: List[dict]) -> Request:
    clock[0] += rng.uniform(3, 25)
    return Request(
        question=question,
        history=list(history),
        now=START + datetime.timedelta(seconds=round(clock[0])),
        request_id="req-%06x" % rng.getrandbits(24),
        tools=_registry(rng),
        at=clock[0],
    )


def single_questions(count: int, seed: int, start: float = 0.0) -> List[Request]:
    """`count` unrelated one-off questions, each from a different user."""
    rng = random.Random(seed)
    clock = [start]
    return [_request(rng, clock, _ask(rng, action, obj), []) for action, obj in _topics(rng, count)]


def conversations(count: int, turns: int, seed: int, start: float = 0.0) -> List[Request]:
    """`count` conversations of `turns` questions each. Every turn is one request."""
    rng = random.Random(seed)
    clock = [start]
    requests = []
    for _ in range(count):
        history: List[dict] = []
        for action, obj in _topics(rng, turns):
            question = _ask(rng, action, obj)
            requests.append(_request(rng, clock, question, history))
            history.append({"role": "user", "text": question})
            history.append({"role": "assistant", "text": _reply(rng, action, obj)})
    return requests


def day_of_traffic(seed: int) -> List[Request]:
    """A scaled-down day: many one-off questions, then a few long conversations."""
    singles = single_questions(120, seed)
    return singles + conversations(4, 30, seed + 1, start=singles[-1].at)
