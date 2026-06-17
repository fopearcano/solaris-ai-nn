"""RC examples: each demo runs, returns 0, and does not loop."""

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


def test_rc_demo_runs(tmp_path):
    _run("run_tester_rc_demo.py", str(tmp_path / "d"))


def test_rc_manifest_demo_runs(tmp_path):
    _run("run_tester_rc_manifest_demo.py", str(tmp_path / "m"))


def test_rc_readiness_demo_runs(tmp_path):
    _run("run_tester_rc_readiness_demo.py", str(tmp_path / "r"))


def test_rc_docs_demo_runs(tmp_path):
    _run("run_tester_rc_docs_demo.py", str(tmp_path / "docs"))


def test_rc_bundle_demo_runs(tmp_path):
    _run("run_tester_rc_bundle_demo.py", str(tmp_path / "b"))
