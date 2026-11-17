"""Small terminal helpers. No dependencies, honors NO_COLOR."""
import os
import sys


def _color() -> bool:
    return sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def _paint(text: str, code: str) -> str:
    return "\033[%sm%s\033[0m" % (code, text) if _color() else text


def bold(text: str) -> str:
    return _paint(text, "1")


def dim(text: str) -> str:
    return _paint(text, "2")


def green(text: str) -> str:
    return _paint(text, "32")


def red(text: str) -> str:
    return _paint(text, "31")


def yellow(text: str) -> str:
    return _paint(text, "33")
