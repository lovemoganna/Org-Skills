#!/usr/bin/env python3
"""Bind the frozen PR #115 scoring harness to the V3 case pack."""
import hashlib
from pathlib import Path
import subprocess
from types import ModuleType

SOURCE = "4c114b27233abd3b04d6bff47f51de4fe3921a13:skills/causal-net-loop/evals/blind12.py"
SOURCE_BLOB = "048b24d5cf2dd1e509cbabc89b07795b45930556"
DATA_BLOB = "1fae196b5a6d44a4b2eebe58db40af02635ae129"


def main():
    here = Path(__file__).resolve()
    repo = here.parents[3]
    source = subprocess.check_output(["git", "show", SOURCE], cwd=repo)
    header = f"blob {len(source)}\0".encode()
    if hashlib.sha1(header + source).hexdigest() != SOURCE_BLOB:
        raise ValueError("Frozen PR #115 harness bytes do not match")
    harness = ModuleType("pr115_blind12")
    harness.__file__ = str(here)
    exec(compile(source, SOURCE, "exec"), vars(harness))
    harness.DATA = here.with_name("blind12-v3-cases.json")
    harness.DATA_BLOB = DATA_BLOB
    harness.main()


if __name__ == "__main__":
    main()
