"""Stand-ins for a coding agent, used to test `womp bench`.

    fake_agent.py solve   copies the reference fix into the working copy
    fake_agent.py noop    changes nothing
"""
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if sys.argv[1:] == ["solve"]:
    solution = ROOT / "exercises" / os.environ["WOMP_EXERCISE"] / ".womp" / "solution"
    shutil.copytree(solution, Path.cwd(), dirs_exist_ok=True)
