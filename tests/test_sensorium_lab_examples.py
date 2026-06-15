"""The five sensorium-lab examples import and run end to end, bounded."""

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


def test_differentiation_demo_runs(tmp_path, capsys):
    mod = _load("run_sensorium_differentiation_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "d")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "sensorium differentiation demo" in out
    assert "does not test consciousness" in out


def test_label_contamination_demo_runs(tmp_path, capsys):
    mod = _load("run_human_label_contamination_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "c")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "human label contamination demo" in out
    assert "never ground truth" in out


def test_modality_fingerprint_demo_runs(tmp_path, capsys):
    mod = _load("run_modality_fingerprint_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "m")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "modality fingerprint demo" in out


def test_world_signature_demo_runs(tmp_path, capsys):
    mod = _load("run_world_signature_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "w")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "world signature demo" in out
    assert "not subjective experience" in out


def test_live_vs_fixture_demo_runs(tmp_path, capsys):
    mod = _load("run_live_vs_fixture_sensorium_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "l")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "live vs fixture sensorium demo" in out
    assert "inconclusive" in out
