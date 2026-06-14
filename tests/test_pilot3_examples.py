"""The six Pilot-3 soak examples import and run end to end, bounded."""

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


def test_soak_plan_runs(tmp_path, capsys):
    mod = _load("run_pilot3_soak_plan")
    sys.argv = ["x", "--output-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "plan only" in out
    assert "real_world_authority : false" in out


def test_firewall_audit_demo_runs(tmp_path, capsys):
    mod = _load("run_pilot3_firewall_audit_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "firewall audit" in out
    assert "real-world executed   : 0" in out


def test_gridworld_soak_demo_runs(tmp_path, capsys):
    mod = _load("run_pilot3_gridworld_soak_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "simulated action/reaction" in out
    assert "no real action occurred" in out


def test_action_grounding_demo_runs(tmp_path, capsys):
    mod = _load("run_pilot3_action_grounding_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "simulation-scoped" in out
    assert "grounding quality" in out


def test_comparative_analysis_demo_runs(tmp_path, capsys):
    mod = _load("run_pilot3_comparative_analysis_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "comparative analysis" in out
    assert "not proven causes" in out


def test_decision_gate_demo_runs(tmp_path, capsys):
    mod = _load("run_pilot3_soak_decision_gate_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "decision gate" in out
    assert "planning-only" in out
