"""The six Pilot-2 examples import and run end to end, bounded."""

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


def test_plan_example(tmp_path, capsys):
    mod = _load("run_pilot2_plan")
    sys.argv = ["x", "--output-dir", str(tmp_path)]
    mod.main()
    assert "plan only" in capsys.readouterr().out.lower()


def test_source_preflight_demo(tmp_path, capsys):
    mod = _load("run_pilot2_source_preflight_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    assert "source preflight" in capsys.readouterr().out.lower()


def test_fixture_short_demo(tmp_path, capsys):
    mod = _load("run_pilot2_fixture_short_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    assert "events ingested" in capsys.readouterr().out.lower()


def test_comparative_demo(tmp_path, capsys):
    mod = _load("run_pilot2_comparative_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "comparative" in out and "not proven causes" in out


def test_grounding_analysis_demo(tmp_path, capsys):
    mod = _load("run_pilot2_grounding_analysis_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    assert "grounding" in capsys.readouterr().out.lower()


def test_decision_gate_demo(tmp_path, capsys):
    mod = _load("run_pilot2_decision_gate_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "decision gate" in out and "planning-only" in out
