"""The five plural-sensorium examples import and run end to end, bounded."""

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


def test_fixture_demo_runs(tmp_path, capsys):
    mod = _load("run_plural_sensorium_fixture_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "ps")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "plural sensorium fixture demo" in out
    assert "no hardware" in out


def test_receptor_adaptation_demo_runs(tmp_path, capsys):
    mod = _load("run_receptor_adaptation_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "ra")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "receptor adaptation demo" in out


def test_cross_modal_demo_runs(tmp_path, capsys):
    mod = _load("run_cross_modal_sensorium_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "cm")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "cross-modal sensorium demo" in out


def test_human_vs_nonhuman_demo_runs(tmp_path, capsys):
    mod = _load("run_human_vs_nonhuman_sensorium_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "hn")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "human vs non-human sensorium demo" in out


def test_grounding_demo_runs(tmp_path, capsys):
    mod = _load("run_sensorium_grounding_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "gr")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "sensorium grounding demo" in out
    assert "no human semantic label" in out
