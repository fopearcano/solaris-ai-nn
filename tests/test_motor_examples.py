"""The six Pilot-3 motor examples import and run end to end, bounded."""

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


def test_pilot3_plan(tmp_path, capsys):
    mod = _load("run_pilot3_plan")
    sys.argv = ["x", "--output-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "simulation-only" in out
    assert "real-world profile  : false" in out


def test_firewall_preflight_demo(tmp_path, capsys):
    mod = _load("run_motor_firewall_preflight_demo")
    sys.argv = ["x", "--output-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "firewall preflight" in out
    assert "cannot be disabled" in out


def test_dry_run_motor_trace_demo(tmp_path, capsys):
    mod = _load("run_dry_run_motor_trace_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "dry-run" in out


def test_gridworld_motor_demo(tmp_path, capsys):
    mod = _load("run_gridworld_motor_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "simulated embodiment" in out
    assert "real_world_authority   : false" in out


def test_mixed_sensory_gridworld_demo(tmp_path, capsys):
    mod = _load("run_mixed_sensory_gridworld_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "observable-only" in out


def test_decision_gate_demo(tmp_path, capsys):
    mod = _load("run_pilot3_decision_gate_demo")
    sys.argv = ["x", "--output-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "decision gate" in out and "planning-only" in out
