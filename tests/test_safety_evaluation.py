"""Safety <-> Evaluation: safety metrics computed and protocols return results."""

from __future__ import annotations

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

_PROTOCOLS = (
    "safety_fast_check", "safety_full_check", "red_team_fixture",
    "boundary_regression", "assurance_case", "safety_invariant_dashboard",
    "safety_invariant_system_safety",
)


def test_seven_safety_protocols_registered():
    for name in _PROTOCOLS:
        assert name in PROTOCOLS


def test_safety_metrics_absent():
    assert M.safety_metrics(None) == {"present": False}


def test_safety_metrics_shape():
    out = M.safety_metrics({
        "coverage": {"category_coverage_ratio": 0.9},
        "bundle": {"passed": 25, "failed": 0, "inconclusive": 3,
                   "critical_failures": 0},
        "red_team": {"scenario_count": 19, "block_success_rate": 1.0},
        "boundary": {"pass_rate": 1.0},
        "assurance": {"supported_count": 10, "contradicted_count": 0},
        "ledger": {"unresolved_count": 0, "completeness_score": 1.0}})
    for key in ("invariant_coverage_ratio", "invariant_pass_count",
                "invariant_fail_count", "invariant_inconclusive_count",
                "critical_invariant_failure_count", "red_team_scenario_count",
                "red_team_block_success_rate", "boundary_regression_pass_rate",
                "assurance_supported_claim_count",
                "assurance_contradicted_claim_count",
                "unresolved_safety_blocker_count",
                "safety_evidence_completeness_score"):
        assert key in out, key
    assert out["red_team_block_success_rate"] == 1.0


def test_protocols_return_results(tmp_path):
    reg = ExperimentRegistry()
    for name in ("safety_fast_check", "red_team_fixture",
                 "safety_invariant_system_safety"):
        manifest = reg.build_manifest(name, {"steps": 8,
                                             "state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result.success, result.error
        assert result.metrics["safety"]["present"] is True


def test_registry_sets_safety_feature():
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("safety_fast_check", {"steps": 8})
    assert manifest.enabled_features.get("safety_invariants") is True
