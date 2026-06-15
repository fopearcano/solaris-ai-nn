"""The five feeder-SDK examples import and run end to end, bounded."""

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


def test_contract_demo_runs(tmp_path, capsys):
    mod = _load("run_feeder_sdk_contract_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "c")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "feeder sdk contract demo" in out
    assert "never ground truth" in out


def test_manifest_demo_runs(tmp_path, capsys):
    mod = _load("run_feeder_pack_manifest_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "m")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "feeder pack manifest demo" in out
    assert "starts no feeder" in out


def test_monitor_demo_runs(tmp_path, capsys):
    mod = _load("run_feeder_monitor_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "mon")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "feeder monitor demo" in out
    assert "silent outputs" in out


def test_replay_demo_runs(tmp_path, capsys):
    mod = _load("run_feeder_replay_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "r")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "feeder replay demo" in out
    assert "replayed marked" in out


def test_simulated_multimodal_demo_runs(tmp_path, capsys):
    mod = _load("run_simulated_multimodal_feeder_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "mm")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "simulated multimodal feeder demo" in out
    assert "not real sensors" in out
