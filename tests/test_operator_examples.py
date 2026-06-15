"""The six operator examples import and run end to end, bounded."""

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


def test_status_demo_runs(tmp_path, capsys):
    mod = _load("run_operator_status_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "op")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "operator status demo" in out
    assert "no real-world authority" in out


def test_profile_plan_demo_runs(tmp_path, capsys):
    mod = _load("run_operator_profile_plan_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "op")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "operator profile-plan demo" in out
    assert "cannot launch" in out


def test_evidence_search_demo_runs(tmp_path, capsys):
    mod = _load("run_operator_evidence_search_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "op")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "evidence-search demo" in out
    assert "no external" in out


def test_next_action_demo_runs(tmp_path, capsys):
    mod = _load("run_operator_next_action_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "op")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "next-action demo" in out
    assert "run_safety_full_check" in out


def test_export_bundle_demo_runs(tmp_path, capsys):
    mod = _load("run_operator_export_bundle_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "op")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "export-bundle demo" in out
    assert "no upload" in out


def test_approval_ledger_demo_runs(tmp_path, capsys):
    mod = _load("run_operator_approval_ledger_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "op")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "approval-ledger demo" in out
    assert "blocked" in out
