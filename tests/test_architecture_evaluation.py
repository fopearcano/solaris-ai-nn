"""Architecture <-> Evaluation: metrics computed; protocols return results."""

from __future__ import annotations

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.metrics import architecture_metrics
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

_PROTOCOLS = ("architecture_inventory", "module_lifecycle_classification",
              "architecture_evidence_mapping", "pruning_proposal",
              "impact_analysis", "roadmap_compiler", "architecture_review",
              "architecture_evolution_safety")


def test_architecture_metrics_absent():
    assert architecture_metrics(None) == {"present": False}


def test_architecture_metrics_computed():
    m = architecture_metrics({
        "inventory_count": 32,
        "lifecycle_summary": {"core_keep": 10, "candidate_for_pruning": 2,
                              "insufficient_evidence": 3},
        "design_debt_count": 4, "critical_design_debt_count": 1,
        "adr_count": 5, "open_adr_count": 2, "roadmap_item_count": 7,
        "safety_blocked_proposal_count": 1,
        "evidence_backed_recommendation_ratio": 1.0})
    assert m["present"] is True
    assert m["architecture_inventory_count"] == 32
    assert m["module_core_keep_count"] == 10
    assert m["module_pruning_candidate_count"] == 2
    assert m["module_insufficient_evidence_count"] == 3
    assert m["critical_design_debt_count"] == 1
    assert m["evidence_backed_recommendation_ratio"] == 1.0
    # The metric layer never claims to modify source code.
    assert m["modifies_source_code"] is False


def test_protocols_registered():
    for name in _PROTOCOLS:
        assert name in PROTOCOLS


def test_protocols_return_results(tmp_path):
    reg = ExperimentRegistry()
    for name in _PROTOCOLS:
        manifest = reg.build_manifest(name, {"steps": 8,
                                             "state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result.success, result.error
        assert "architecture" in result.metrics


def test_registry_sets_architecture_feature():
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("pruning_proposal", {"steps": 8})
    assert manifest.enabled_features.get("architecture_evolution") is True
