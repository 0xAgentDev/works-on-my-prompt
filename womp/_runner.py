"""Runs one exercise's held-out checks inside a grading sandbox.

womp.grading starts this file in a subprocess: `python _runner.py <sandbox>`. The sandbox's
.womp/checks.py exposes CHECKS, a list of (criterion_id, function). Each function returns
(passed, detail). One crashing or hanging check never takes the others down with it.
"""
import importlib.util
import json
import os
import signal
import sys
import traceback

MARK = "WOMP_RESULTS "
PER_CHECK_SECONDS = 60


class _Timeout(Exception):
    pass


def _on_alarm(signum, frame):
    raise _Timeout()


def _describe(exc):
    """A one-line error that points at the user's code when it can."""
    where = ""
    for frame in reversed(traceback.extract_tb(exc.__traceback__)):
        if os.sep + "app" + os.sep in frame.filename:
            where = " (app/%s:%d)" % (os.path.basename(frame.filename), frame.lineno)
            break
    text = str(exc).strip()
    message = text.splitlines()[0] if text else ""
    return "%s: %s%s" % (type(exc).__name__, message, where) if message else type(exc).__name__ + where


def main(box):
    sys.path.insert(0, box)
    os.chdir(box)
    try:
        spec = importlib.util.spec_from_file_location("womp_checks", os.path.join(box, ".womp", "checks.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        checks = module.CHECKS
    except BaseException as exc:  # a syntax error in app/ lands here
        print(MARK + json.dumps({"error": "could not load your app: " + _describe(exc)}))
        return
    can_alarm = hasattr(signal, "SIGALRM")
    results = []
    for criterion_id, check in checks:
        try:
            if can_alarm:
                signal.signal(signal.SIGALRM, _on_alarm)
                signal.alarm(PER_CHECK_SECONDS)
            passed, detail = check()
        except _Timeout:
            passed, detail = False, "timed out after %ds: is something looping forever?" % PER_CHECK_SECONDS
        except Exception as exc:
            passed, detail = False, _describe(exc)
        finally:
            if can_alarm:
                signal.alarm(0)
        results.append({"id": criterion_id, "passed": bool(passed), "detail": str(detail)})
    print(MARK + json.dumps(results))


if __name__ == "__main__":
    main(os.path.abspath(sys.argv[1]))
