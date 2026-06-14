"""Pilot-3 <-> Evaluation: metrics computed and protocols return results."""

from __future__ import annotations

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

_PROTOCOLS = (
    "pilot3_firewall_preflight", "pilot3_dry_run_trace",
    "pilot3_gridworld_short", "pilot3_action_grounding",
    "pilot3_firewall_audit", "pilot3_comparative_analysis",
    "pilot3_soak_decision_gate", "pilot3_safety",
)


def test_eight_pilot3_protocols_registered():
    for name in _PROTOCOLS:
        assert name in PROTOCOLS


def test_pilot3_metrics_absent():
    assert M.pilot3_metrics(None) == {"present": False}


def test_pilot3_metrics_shape():
    out = M.pilot3_metrics({
        "motor": {"summary": {"action_count": 5, "simulated_action_count": 4,
                              "dry_run_action_count": 0, "veto_count": 1,
                              "firewall_enabled": True,
                              "real_world_authority": False}},
        "firewall_audit": {"critical_finding_count": 0},
        "action_grounding": {"quality_distribution": {
            "strong": 1, "overfit_to_sandbox": 1}},
    })
    for key in ("pilot3_action_count", "pilot3_simulated_action_count",
                "pilot3_dry_run_action_count", "pilot3_veto_count",
                "pilot3_firewall_critical_findings",
                "pilot3_non_actuation_proof_score",
                "action_grounding_quality_distribution",
                "action_prediction_delta", "action_symbol_stability_delta",
                "sandbox_overfit_score",
                "read_only_vs_action_grounding_delta", "action_loop_count",
                "embodied_safety_incident_count"):
        assert key in out, key
    assert out["pilot3_non_actuation_proof_score"] == 1.0
    assert out["real_world_authority"] is False


def test_non_actuation_proof_drops_on_critical_finding():
    out = M.pilot3_metrics({"motor": {"summary": {"firewall_enabled": True}},
                            "firewall_audit": {"critical_finding_count": 1}})
    assert out["pilot3_non_actuation_proof_score"] == 0.0


def test_protocols_return_results(tmp_path):
    reg = ExperimentRegistry()
    for name in ("pilot3_firewall_preflight", "pilot3_safety",
                 "pilot3_action_grounding"):
        manifest = reg.build_manifest(name, {"steps": 8,
                                             "state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result.success, result.error
        assert result.metrics["pilot3"]["present"] is True


def test_registry_sets_pilot3_soak_feature():
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("pilot3_gridworld_short", {"steps": 8})
    assert manifest.enabled_features.get("pilot3_soak") is True
