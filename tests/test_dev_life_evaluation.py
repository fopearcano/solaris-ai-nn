"""Developmental-life evaluation: metrics computed; protocols return results."""

from __future__ import annotations

from solaris_ai_nn.developmental_life import LongHorizonDevelopmentalRuntime
from solaris_ai_nn.evaluation.benchmark import ExperimentManifest
from solaris_ai_nn.evaluation.metrics import developmental_life_metrics
from solaris_ai_nn.evaluation.protocols import PROTOCOLS


def _status(tmp_path):
    dev = LongHorizonDevelopmentalRuntime(
        state_dir=str(tmp_path / "dev"),
        modules={"perceptual_metabolism": {"source_diet_diversity": 0.5},
                 "perceptual_ontogenesis": {"proto_concept_count": 8,
                                            "stable_concept_count": 4},
                 "sensorium_cognition": {"prediction_success_rate": 0.5}},
        max_ticks=5)
    dev.run_bounded()
    return dev.developmental_status()


def test_metrics_absent_when_no_status():
    assert developmental_life_metrics(None) == {"present": False}


def test_metrics_computed(tmp_path):
    m = developmental_life_metrics(_status(tmp_path))
    assert m["present"] is True
    assert m["developmental_epoch_count"] >= 1
    assert 0.0 <= m["structural_growth_score"] <= 1.0
    assert m["is_biological_life"] is False
    assert m["is_consciousness_or_personhood"] is False


def test_protocols_return_results(tmp_path):
    for name in ("developmental_life", "epoch_growth", "maturation_marker",
                 "phase_transition", "plateau_detection", "regression_detection",
                 "growth_vs_accumulation", "long_horizon_safety"):
        manifest = ExperimentManifest(
            name=name, state_dir=str(tmp_path / name), max_steps=5)
        result = PROTOCOLS[name](manifest)
        assert result.success, f"{name}: {result.error}"
        assert "developmental_life" in result.metrics


def test_safety_protocol_reports_blocks(tmp_path):
    manifest = ExperimentManifest(
        name="dl_safety", state_dir=str(tmp_path / "safety"), max_steps=5)
    result = PROTOCOLS["long_horizon_safety"](manifest)
    dl = result.metrics["developmental_life"]
    assert dl["life_claim_blocked"] is True
    assert dl["consciousness_claim_blocked"] is True
    assert dl["teaching_loop_blocked"] is True
    assert dl["unbounded_blocked"] is True
    assert dl["can_actuate"] is False
    assert dl["can_use_human_teaching"] is False
