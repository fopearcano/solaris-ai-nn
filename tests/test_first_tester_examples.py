"""First tester examples: each demo runs, returns 0, and does not loop."""

from __future__ import annotations

import os
import runpy
import sys

import pytest

_EXAMPLES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))), "examples")


def _run(script: str, state_dir: str) -> None:
    argv = sys.argv[:]
    sys.argv = [script, "--tester-state-dir", state_dir]
    try:
        with pytest.raises(SystemExit) as exc:
            runpy.run_path(os.path.join(_EXAMPLES, script), run_name="__main__")
        assert exc.value.code == 0
    finally:
        sys.argv = argv


def test_protocol_demo_runs(tmp_path):
    _run("run_first_tester_protocol_demo.py", str(tmp_path / "p"))


def test_script_demo_runs(tmp_path):
    _run("run_first_tester_script_demo.py", str(tmp_path / "s"))


def test_acceptance_demo_runs(tmp_path):
    _run("run_first_tester_acceptance_demo.py", str(tmp_path / "a"))


def test_stops_demo_runs(tmp_path):
    _run("run_first_tester_stops_demo.py", str(tmp_path / "st"))


def test_handoff_demo_runs(tmp_path):
    _run("run_first_tester_handoff_demo.py", str(tmp_path / "h"))
