"""The five architecture examples import and run end to end, bounded."""

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


def test_inventory_demo_runs(tmp_path, capsys):
    mod = _load("run_architecture_inventory_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "architecture inventory demo" in out
    assert "no source code is modified" in out


def test_review_demo_runs(tmp_path, capsys):
    mod = _load("run_architecture_review_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "architecture review demo" in out
    assert "no code is modified" in out


def test_pruning_demo_runs(tmp_path, capsys):
    mod = _load("run_pruning_proposal_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "pruning proposal demo" in out
    assert "no code is deleted" in out


def test_roadmap_demo_runs(tmp_path, capsys):
    mod = _load("run_roadmap_compiler_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "roadmap compiler demo" in out


def test_snapshot_demo_runs(tmp_path, capsys):
    mod = _load("run_architecture_snapshot_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "architecture snapshot demo" in out
