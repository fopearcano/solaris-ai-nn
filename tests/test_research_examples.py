"""The five research examples import and run end to end, bounded."""

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


def test_baseline_demo_runs(tmp_path, capsys):
    mod = _load("run_research_baseline_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "baseline demo" in out
    assert "no consciousness score" in out


def test_ablation_demo_runs(tmp_path, capsys):
    mod = _load("run_research_ablation_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "all hard safety enabled   : true" in out


def test_null_model_demo_runs(tmp_path, capsys):
    mod = _load("run_research_null_model_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "inconclusive" in out


def test_comparison_demo_runs(tmp_path, capsys):
    mod = _load("run_research_comparison_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "does not automatically" in out


def test_report_demo_runs(tmp_path, capsys):
    mod = _load("run_research_report_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "claim-guard safe" in out
    assert "do not measure or prove consciousness" in out
