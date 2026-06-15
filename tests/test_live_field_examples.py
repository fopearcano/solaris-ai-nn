"""The five live-field examples import and run end to end, bounded."""

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


def test_preflight_demo_runs(tmp_path, capsys):
    mod = _load("run_live_field_preflight_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "p")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "live field preflight demo" in out
    assert "live mode needs" in out or "governance" in out


def test_fixture_fallback_demo_runs(tmp_path, capsys):
    mod = _load("run_live_field_fixture_fallback_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "f")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "fixture fallback demo" in out
    assert "no hardware" in out


def test_report_demo_runs(tmp_path, capsys):
    mod = _load("run_live_field_report_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "r")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "live field report demo" in out
    assert "corrupt" in out


def test_comparison_demo_runs(tmp_path, capsys):
    mod = _load("run_live_field_comparison_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "c")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "live field comparison demo" in out


def test_feeder_contract_demo_runs(tmp_path, capsys):
    mod = _load("run_feeder_contract_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "fc")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "feeder contract demo" in out
    assert "provenance present" in out
