"""The six Pilot-1 examples import and run end to end, bounded (no long run)."""

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
    mod = _load("run_pilot1_plan")
    sys.argv = ["x", "--output-dir", str(tmp_path)]
    mod.main()
    assert "plan only" in capsys.readouterr().out.lower()


def test_preflight_example(tmp_path, capsys):
    mod = _load("run_pilot1_preflight")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    assert "preflight" in capsys.readouterr().out.lower()


def test_dashboard_example(tmp_path, capsys):
    mod = _load("run_pilot1_dashboard_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    assert "dashboard" in capsys.readouterr().out.lower()


def test_restart_drill_example(tmp_path, capsys):
    mod = _load("run_pilot1_restart_drill_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    assert "restart drill" in capsys.readouterr().out.lower()


def test_daily_review_example(tmp_path, capsys):
    mod = _load("run_pilot1_daily_review_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    assert "daily review" in capsys.readouterr().out.lower()


def test_exit_criteria_example(tmp_path, capsys):
    mod = _load("run_pilot1_exit_criteria_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out
    assert "success" in out.lower() and "consciousness" in out.lower()
