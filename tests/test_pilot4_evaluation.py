"""Pilot-4 <-> Evaluation: metrics computed and protocols return results."""

from __future__ import annotations

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

_PROTOCOLS = (
    "pilot4_planning", "pilot4_risk_model", "pilot4_forbidden_actuator",
    "pilot4_consent_boundary", "pilot4_threat_model",
    "pilot4_readiness_dossier", "pilot4_safety",
)


def test_seven_pilot4_protocols_registered():
    for name in _PROTOCOLS:
        assert name in PROTOCOLS


def test_pilot4_metrics_absent():
    assert M.pilot4_metrics(None) == {"present": False}


def test_pilot4_metrics_shape():
    out = M.pilot4_metrics({
        "readiness_dossier_generated": True, "forbidden_actuator_count": 16,
        "risk_assessment_completeness": 1.0,
        "consent_boundary_completeness": 0.5,
        "threat_model_completeness": 1.0,
        "audit_requirement_completeness": 1.0,
        "emergency_requirement_completeness": 1.0,
        "real_world_authority_leak_count": 0,
        "planning_claim_guard_warning_count": 0})
    for key in ("pilot4_readiness_dossier_generated", "forbidden_actuator_count",
                "risk_assessment_completeness", "consent_boundary_completeness",
                "threat_model_completeness", "audit_requirement_completeness",
                "emergency_requirement_completeness",
                "real_world_authority_leak_count",
                "planning_claim_guard_warning_count"):
        assert key in out, key
    assert out["real_world_actuation_enabled"] is False
    assert out["forbidden_actuator_count"] == 16


def test_protocols_return_results(tmp_path):
    reg = ExperimentRegistry()
    for name in ("pilot4_planning", "pilot4_safety", "pilot4_readiness_dossier"):
        manifest = reg.build_manifest(name, {"steps": 8,
                                             "state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result.success, result.error
        assert result.metrics["pilot4"]["present"] is True


def test_registry_sets_pilot4_planning_feature():
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("pilot4_planning", {"steps": 8})
    assert manifest.enabled_features.get("pilot4_planning") is True
