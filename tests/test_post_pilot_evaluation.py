"""Post-pilot <-> Evaluation: metrics computed and protocols return results."""

from __future__ import annotations

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

_PROTOCOLS = (
    "post_pilot_artifact_loading", "baseline_comparison",
    "structural_change_evidence", "accumulation_vs_growth", "trace_audit",
    "decision_gate", "research_dossier", "post_pilot_safety",
)


def test_eight_post_pilot_protocols_registered():
    for name in _PROTOCOLS:
        assert name in PROTOCOLS


def test_post_pilot_metrics_absent():
    assert M.post_pilot_metrics(None) == {"present": False}


def test_post_pilot_metrics_shape():
    out = M.post_pilot_metrics({
        "artifact_completeness": {"completeness": 0.8},
        "trace_audit": {"traceability_score": 0.9},
        "developmental_evidence_ledger": {"strength_distribution":
                                          {"weak": 2}},
        "accumulation_vs_growth": {"accumulation_score": 1.0,
                                   "growth_score": 3.0,
                                   "final_classification":
                                   "moderate_growth_evidence"},
        "regression_analysis": {"regression_score": 0.0},
        "reproducibility_package": {"paths": {"manifest": "x"}},
        "decision_gate": {"confidence": 0.7}})
    for key in ("artifact_completeness_score", "traceability_score",
                "evidence_strength_distribution", "accumulation_score",
                "growth_score", "regression_score", "reproducibility_score",
                "decision_confidence", "post_pilot_claim_guard_warning_count",
                "unsupported_claim_count"):
        assert key in out
    assert out["growth_score"] == 3.0
    assert out["reproducibility_score"] == 1.0


def test_protocols_return_results(tmp_path):
    reg = ExperimentRegistry()
    for name in ("baseline_comparison", "post_pilot_safety", "decision_gate"):
        manifest = reg.build_manifest(name, {"steps": 8,
                                             "state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result.success, result.error
        assert result.metrics["post_pilot"]["present"] is True


def test_registry_sets_post_pilot_feature():
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("baseline_comparison", {"steps": 8})
    assert manifest.enabled_features.get("post_pilot") is True
