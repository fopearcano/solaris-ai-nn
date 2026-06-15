"""The four organismic-demo examples import and run end to end, bounded."""

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


def test_minimal_field_organism_demo_runs(tmp_path, capsys):
    mod = _load("run_minimal_field_organism_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "m"), "--ticks", "40"]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "minimal field organism demo" in out
    assert "does not prove consciousness" in out


def test_changed_perception_probe_demo_runs(tmp_path, capsys):
    mod = _load("run_changed_perception_probe_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "c")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "changed perception probe demo" in out
    assert "changed-perception score" in out


def test_organismic_comparison_demo_runs(tmp_path, capsys):
    mod = _load("run_organismic_comparison_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "cmp")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "organismic comparison demo" in out
    assert "passive" in out


def test_external_feeder_contract_demo_runs(tmp_path, capsys):
    mod = _load("run_external_feeder_contract_demo")
    sys.argv = ["x", "--state-dir", str(tmp_path / "f")]
    mod.main()
    out = capsys.readouterr().out.lower()
    assert "external feeder contract demo" in out
    assert "debug-truth excluded" in out
