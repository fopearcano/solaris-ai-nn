"""SensoriumStructureMetrics: computed; no consciousness/sentience/life score."""

from __future__ import annotations

from solaris_ai_nn.sensorium_lab import (
    SensoriumDifferentiationRunner,
    SensoriumStructureMetrics,
    SensoriumStudyArm,
    SensoriumStudyCondition,
    SensoriumStudyDesign,
)
from solaris_ai_nn.sensorium_lab.sensorium_profiles import SensoriumProfileType as P


def _metrics(tmp_path):
    design = SensoriumStudyDesign(ticks=40, max_events=200)
    design.add_arm(SensoriumStudyArm(
        arm_id="mixed", condition=SensoriumStudyCondition.MIXED_PLURAL_SENSORIUM,
        profile_type=P.MIXED_HUMAN_NONHUMAN))
    runner = SensoriumDifferentiationRunner(state_dir=str(tmp_path / "lab"),
                                            design=design)
    runner.prepare_study(design)
    runner.run_all()
    return runner.arm_results["mixed"].metrics


def test_metrics_computed(tmp_path):
    m = _metrics(tmp_path)
    flat = m.flat()
    assert "active_modality_count" in flat
    assert "proto_symbol_count" in flat
    assert "world_node_count" in flat
    assert "changed_perception_score" in flat
    assert "modality_native_grounding_score" in flat


def test_no_forbidden_scores(tmp_path):
    m = _metrics(tmp_path)
    blob = str(m.to_dict()).lower()
    for forbidden in ("consciousness", "sentience_score", "life_score",
                      "intelligence_quotient", "iq_score"):
        assert forbidden not in m.flat()
    assert "no consciousness/sentience/life score" in m.to_dict()["note"]


def test_passive_metrics_are_zero():
    m = SensoriumStructureMetrics.compute(None, passive=True)
    assert m.flat()["proto_symbol_count"] == 0
    assert m.flat()["changed_perception_score"] == 0.0
