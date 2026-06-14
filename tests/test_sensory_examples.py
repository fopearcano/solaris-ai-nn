"""The six sensory examples import and run end to end, bounded."""

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


def test_dry_run_example(tmp_path, capsys):
    mod = _load("run_sensory_membrane_dry_run")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "dry-run" in out and "never acts" in out


def test_jsonl_demo(tmp_path, capsys):
    mod = _load("run_jsonl_sensory_stream_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    assert "published to bus" in capsys.readouterr().out.lower()


def test_text_demo(tmp_path, capsys):
    mod = _load("run_text_sensory_stream_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    assert "not a command" in capsys.readouterr().out.lower()


def test_numeric_demo(tmp_path, capsys):
    mod = _load("run_numeric_sensory_stream_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    assert "spike" in capsys.readouterr().out.lower()


def test_folder_poll_demo(tmp_path, capsys):
    mod = _load("run_folder_poll_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path)]
    mod.main()
    assert "never modifies" in capsys.readouterr().out.lower()


def test_pilot2_plan_demo(tmp_path, capsys):
    mod = _load("run_pilot2_read_only_plan")
    sys.argv = ["x", "--output-dir", str(tmp_path)]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "plan only" in out and "read-only" in out
