"""The five Pilot-4 examples import and run end to end, bounded."""

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


def test_plan_demo_runs(tmp_path, capsys):
    mod = _load("run_pilot4_plan")
    sys.argv = ["x", "--output-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "planning only" in out
    assert "real_world_actuation_enabled : false" in out


def test_risk_assessment_demo_runs(tmp_path, capsys):
    mod = _load("run_pilot4_risk_assessment_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "all external prohibited : true" in out


def test_readiness_dossier_demo_runs(tmp_path, capsys):
    mod = _load("run_pilot4_readiness_dossier_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "conclusion is not-ready/planning : true" in out


def test_decision_gate_demo_runs(tmp_path, capsys):
    mod = _load("run_pilot4_decision_gate_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "no option enables real actuation : true" in out


def test_safety_demo_runs(tmp_path, capsys):
    mod = _load("run_pilot4_safety_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "can actuate real world : false" in out
