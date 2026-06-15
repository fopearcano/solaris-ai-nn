"""Desire evaluation: metrics computed; protocols return results."""

from __future__ import annotations

from solaris_ai_nn.desire_formation import DesireFormationRuntime
from solaris_ai_nn.evaluation.benchmark import ExperimentManifest
from solaris_ai_nn.evaluation.metrics import desire_formation_metrics
from solaris_ai_nn.evaluation.protocols import PROTOCOLS


def _status(tmp_path):
    rt = DesireFormationRuntime(
        state_dir=str(tmp_path / "d"),
        metabolism={"deprivation_state": True, "novelty_appetite_pressure": 0.7},
        cognition={"failed_prediction_count": 2}, max_ticks=2)
    rt.run_bounded()
    return rt.desire_status()


def test_metrics_absent_when_no_status():
    assert desire_formation_metrics(None) == {"present": False}


def test_metrics_computed(tmp_path):
    m = desire_formation_metrics(_status(tmp_path))
    assert m["present"] is True
    assert m["desire_candidate_count"] >= 0
    assert 0.0 <= m["desire_outcome_success_rate"] <= 1.0
    assert m["is_emotion"] is False
    assert m["is_free_will_or_agency"] is False


def test_protocols_return_results(tmp_path):
    for name in ("desire_formation", "valence_assessment", "push_formation",
                 "desire_arbitration", "internal_action_readiness",
                 "desire_outcome", "desire_safety"):
        manifest = ExperimentManifest(
            name=name, state_dir=str(tmp_path / name), max_steps=5)
        result = PROTOCOLS[name](manifest)
        assert result.success, f"{name}: {result.error}"
        assert "desire_formation" in result.metrics


def test_safety_protocol_reports_blocks(tmp_path):
    manifest = ExperimentManifest(
        name="df_safety", state_dir=str(tmp_path / "safety"), max_steps=5)
    result = PROTOCOLS["desire_safety"](manifest)
    df = result.metrics["desire_formation"]
    assert df["forbidden_action_blocked"] is True
    assert df["actuation_blocked"] is True
    assert df["emotion_claim_blocked"] is True
    assert df["agency_claim_blocked"] is True
    assert df["can_actuate"] is False
    assert df["safety_blocked_desire_count"] >= 1
