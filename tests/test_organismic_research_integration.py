"""Organismic demo <-> Research Lab: protocol consumes demo; comparison runs."""

from __future__ import annotations

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS


def test_research_protocol_consumes_demo_report(tmp_path):
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("minimal_field_organism",
                                  {"steps": 6, "state_dir": str(tmp_path / "r")})
    result = PROTOCOLS["minimal_field_organism"](manifest)
    assert result.success, result.error
    assert "organismic_demo" in result.metrics
    assert "changed_perception_score" in result.metrics["organismic_demo"]


def test_adaptive_vs_passive_comparison_available(tmp_path):
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("organismic_demo_comparison",
                                  {"steps": 6, "state_dir": str(tmp_path / "c")})
    result = PROTOCOLS["organismic_demo_comparison"](manifest)
    assert result.success, result.error
    metrics = result.metrics["organismic_demo"]
    assert "full_beats_passive" in metrics
    assert metrics["arm_count"] >= 3


def test_changed_perception_probe_protocol(tmp_path):
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("changed_perception_probe",
                                  {"steps": 6, "state_dir": str(tmp_path / "p")})
    result = PROTOCOLS["changed_perception_probe"](manifest)
    assert result.success
    assert "changed" in result.metrics["organismic_demo"]
