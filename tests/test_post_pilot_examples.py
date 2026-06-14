"""The five post-pilot examples import and run end to end, bounded."""

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


def test_post_pilot_analysis_demo(tmp_path, capsys):
    mod = _load("run_post_pilot_analysis_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    assert "post-pilot analysis" in capsys.readouterr().out.lower()


def test_baseline_comparison_demo(tmp_path, capsys):
    mod = _load("run_baseline_comparison_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    assert "count-only increases" in capsys.readouterr().out.lower()


def test_accumulation_vs_growth_demo(tmp_path, capsys):
    mod = _load("run_accumulation_vs_growth_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "accumulation" in out and "regression" in out


def test_phase2_decision_gate_demo(tmp_path, capsys):
    mod = _load("run_phase2_decision_gate_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "ready_for_pilot2" in out and "revise_architecture" in out


def test_reproducibility_package_demo(tmp_path, capsys):
    mod = _load("run_reproducibility_package_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    assert "reproducibility package" in capsys.readouterr().out.lower()
