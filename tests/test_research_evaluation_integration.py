"""Research <-> Evaluation: protocols return results; metrics connect."""

from __future__ import annotations

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

_PROTOCOLS = ("research_baseline", "research_ablation", "research_null_model",
              "research_comparison", "research_module_effect",
              "research_reproducibility", "research_report")


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
        assert "research" in result.metrics


def test_registry_sets_research_feature():
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("research_baseline", {"steps": 8})
    assert manifest.enabled_features.get("research_lab") is True


def test_metrics_connect_to_evaluation(tmp_path):
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("research_report", {"steps": 8,
                                                      "state_dir": str(tmp_path)})
    result = PROTOCOLS["research_report"](manifest)
    assert result.metrics["research"]["claim_guard_safe"] is True
