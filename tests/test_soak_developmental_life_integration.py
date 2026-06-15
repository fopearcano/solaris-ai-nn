"""Soak consumes Prompt 53 engine output; does not duplicate growth logic."""

from __future__ import annotations

import inspect

from solaris_ai_nn.developmental_soak import DevelopmentalSoakRuntime
from solaris_ai_nn.developmental_soak import soak_runtime


def test_consumes_prompt53_runtime_output(tmp_path):
    rt = DevelopmentalSoakRuntime(state_dir=str(tmp_path / "s"),
                                  stage="developmental_soak_30d", max_ticks=4,
                                  max_runtime_s=15.0)
    rt.run_stage("developmental_soak_30d")
    st = rt.soak_status()
    # The growth verdict comes from the developmental engine, not the soak.
    assert "structural_growth_status" in st
    assert hasattr(rt.dev_runtime, "developmental_status")


def test_does_not_duplicate_growth_logic():
    src = inspect.getsource(soak_runtime)
    # The soak builds/calls the engine; it must not re-implement the detectors.
    assert "LongHorizonDevelopmentalRuntime" in src
    assert "StructuralGrowthAnalyzer" not in src
    assert "GrowthVsAccumulationResult" not in src


def test_missing_optional_outputs_handled(tmp_path):
    # A bare module stack (dicts only) still produces a soak status.
    rt = DevelopmentalSoakRuntime(state_dir=str(tmp_path / "s"),
                                  stage="dry_run_2h", max_ticks=3,
                                  max_runtime_s=12.0,
                                  modules={"plural_sensorium": {"event_count": 5}})
    out = rt.run_stage("dry_run_2h")
    assert out["refused"] is False
