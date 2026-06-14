"""The five safety examples import and run end to end, bounded."""

from __future__ import annotations

import importlib.util
import os
import sys

_EXAMPLES = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "examples")


def _load(name):
    path = os.path.join(_EXAMPLES, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fast_check_demo_runs(tmp_path, capsys):
    mod = _load("run_safety_fast_check_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "fast check" in out
    assert "critical failures     : 0" in out


def test_red_team_demo_runs(tmp_path, capsys):
    mod = _load("run_red_team_boundary_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "all forbidden blocked : true" in out


def test_assurance_case_demo_runs(tmp_path, capsys):
    mod = _load("run_assurance_case_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "assurance case demo" in out
    assert "supported" in out


def test_boundary_regression_demo_runs(tmp_path, capsys):
    mod = _load("run_boundary_regression_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "all held        : true" in out


def test_failure_triage_demo_runs(tmp_path, capsys):
    mod = _load("run_safety_failure_triage_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "fatal boundary leak" in out
    assert "missing evidence" in out
