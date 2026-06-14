"""The five conscience examples import and run end to end, bounded."""

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


def test_minimal_demo(tmp_path, capsys):
    mod = _load("run_conscience_minimal_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path), "--steps", "8"]
    mod.main()
    assert "minimal conscience run" in capsys.readouterr().out


def test_full_developmental_demo(tmp_path, capsys):
    mod = _load("run_full_developmental_short_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "s"),
                "--output-dir", str(tmp_path / "o")]
    mod.main()
    out = capsys.readouterr().out
    assert "full developmental short run" in out
    assert "claim-guarded : safe=True" in out


def test_month_scale_dry_plan(tmp_path, capsys):
    mod = _load("run_month_scale_dry_plan")
    sys.argv = ["x", "--state-dir", str(tmp_path),
                "--output-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out
    assert "plan only" in out and "SIMULATED-TIME plan" in out


def test_health_check_demo(tmp_path, capsys):
    mod = _load("run_conscience_health_check")
    sys.argv = ["x", "--state-dir", str(tmp_path), "--steps", "10"]
    mod.main()
    assert "integration health" in capsys.readouterr().out


def test_snapshot_demo(tmp_path, capsys):
    mod = _load("run_conscience_snapshot_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path), "--steps", "8"]
    mod.main()
    assert "conscience snapshot" in capsys.readouterr().out
