"""Soak evaluation: metrics computed; protocols return results."""

from __future__ import annotations

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS


def test_metrics_computed():
    metrics = M.developmental_soak_metrics({
        "soak_stage_count": 7, "checkpoint_count": 2, "daily_packet_count": 1,
        "evidence_claim_count": 4, "structural_growth_status": "inconclusive"})
    assert metrics["present"] is True
    assert metrics["soak_stage_count"] == 7
    assert metrics["is_biological_life"] is False
    assert metrics["is_consciousness_or_personhood"] is False


def test_metrics_absent_when_empty():
    assert M.developmental_soak_metrics(None) == {"present": False}


def test_protocols_return_results(tmp_path):
    reg = ExperimentRegistry()
    for name in ("developmental_soak", "soak_preflight_protocol",
                 "checkpoint_evaluation", "daily_packet_protocol",
                 "weekly_review_protocol", "restart_drill_protocol",
                 "control_arm_protocol", "evidence_dossier_protocol",
                 "post_run_autopsy_protocol", "developmental_soak_safety"):
        manifest = reg.build_manifest(name, {"state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result is not None
        assert "developmental_soak" in result.metrics


def test_feature_flag_set(tmp_path):
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("developmental_soak_protocol",
                                  {"state_dir": str(tmp_path)})
    assert manifest.enabled_features.get("developmental_soak") is True


def test_safety_protocol_blocks(tmp_path):
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("developmental_soak_safety",
                                  {"state_dir": str(tmp_path)})
    res = PROTOCOLS["developmental_soak_safety"](manifest)
    ds = res.metrics["developmental_soak"]
    assert ds["unbounded_daemon_blocked"] is True
    assert ds["actuation_blocked"] is True
    assert ds["life_claim_blocked"] is True
