"""Sensorium lab <-> organismic demo: passive/no-adaptation baselines included."""

from __future__ import annotations

from solaris_ai_nn.sensorium_lab import (
    SensoriumDifferentiationRunner,
    default_study_design,
)


def _runner(tmp_path):
    design = default_study_design()
    design.ticks = 40
    runner = SensoriumDifferentiationRunner(state_dir=str(tmp_path / "lab"),
                                            design=design)
    runner.prepare_study(design)
    runner.run_all()
    return runner


def test_passive_baseline_included(tmp_path):
    runner = _runner(tmp_path)
    assert "passive" in runner.arm_results
    passive = runner.arm_results["passive"]
    assert passive.passive is True
    assert passive.metrics.flat()["proto_symbol_count"] == 0


def test_adaptive_baseline_included(tmp_path):
    runner = _runner(tmp_path)
    assert "adaptive" in runner.arm_results
    adaptive = runner.arm_results["adaptive"]
    assert adaptive.metrics.flat()["proto_symbol_count"] >= 0


def test_passive_vs_adaptive_comparable(tmp_path):
    runner = _runner(tmp_path)
    comparison = runner.compare_results()
    diff = next((d for d in comparison.differences
                 if d.arm_a == "passive" and d.arm_b == "adaptive"), None)
    assert diff is not None
    # Passive forms no structure; adaptive does -> a real difference.
    assert diff.strength != "inconclusive"
