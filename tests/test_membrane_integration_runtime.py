"""Integration runtime: runs bounded, writes artifacts, blocks strict bypass."""

from __future__ import annotations

import json
import os
import sys

from solaris_ai_nn.membrane_integration import MembraneIntegrationRuntime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _membrane_integration_helpers import stage_pipeline  # noqa: E402


def test_runtime_runs_clean_pipeline(tmp_path):
    state = stage_pipeline(str(tmp_path))
    rt = MembraneIntegrationRuntime(
        state_dir=state, profile="fixture_integration_v0")
    result = rt.run()
    assert result["refused"] is False
    assert result["blocked"] is False
    assert result["membrane_present"] is True
    assert result["impression_count"] == 4
    assert result["ancestry_chain_count"] >= 3
    assert result["critical_bypass_count"] == 0


def test_runtime_writes_artifacts(tmp_path):
    state = stage_pipeline(str(tmp_path))
    rt = MembraneIntegrationRuntime(
        state_dir=state, profile="fixture_integration_v0")
    rt.run()
    base = os.path.join(state, "membrane", "integration")
    for name in ("MEMBRANE_INTEGRATION_REPORT.md",
                 "MEMBRANE_INTEGRATION_REPORT.json",
                 "MEMBRANE_DOWNSTREAM_CONTRACTS.md",
                 "MEMBRANE_BYPASS_REPORT.md", "MEMBRANE_ANCESTRY_REPORT.md",
                 "MEMBRANE_PIPELINE_AUDIT.md",
                 "MEMBRANE_INTEGRATION_SAFETY_REPORT.md"):
        assert os.path.isfile(os.path.join(base, name)), name
    runs = [f for f in os.listdir(base)
            if f.startswith("integ_") and f.endswith(".json")]
    assert runs
    status = json.load(open(os.path.join(base, runs[-1])))
    assert status["membrane_integration_enabled"] is True
    assert status["starts_feeders"] is False
    assert status["controls_hardware"] is False


def test_unbounded_runtime_refused(tmp_path):
    state = stage_pipeline(str(tmp_path))
    rt = MembraneIntegrationRuntime(state_dir=state, max_runtime_s=0)
    result = rt.run()
    assert result["refused"] is True


def test_dry_run_writes_nothing(tmp_path):
    state = stage_pipeline(str(tmp_path))
    rt = MembraneIntegrationRuntime(
        state_dir=state, profile="fixture_integration_v0", dry_run=True)
    rt.run()
    base = os.path.join(state, "membrane", "integration")
    assert not os.path.isfile(
        os.path.join(base, "MEMBRANE_INTEGRATION_REPORT.md"))


def test_strict_enforced_blocks_missing_ancestry(tmp_path):
    state = stage_pipeline(str(tmp_path), include_bypass=True)
    rt = MembraneIntegrationRuntime(
        state_dir=state, profile="live_integration_enforced_v0")
    result = rt.run()
    assert rt.strict is True
    assert result["blocked"] is True
    assert result["critical_bypass_count"] >= 1


def test_doctor_reports_state(tmp_path):
    state = stage_pipeline(str(tmp_path))
    rt = MembraneIntegrationRuntime(
        state_dir=state, profile="fixture_integration_v0")
    doc = rt.run_doctor()
    assert doc["membrane_present"] is True
    assert doc["impressions_present"] is True
    assert doc["bounded"] is True


def test_recommended_next_action_clean(tmp_path):
    state = stage_pipeline(str(tmp_path))
    rt = MembraneIntegrationRuntime(
        state_dir=state, profile="fixture_integration_v0")
    rt.run()
    action = rt.recommended_next_action()
    assert "observation" in action.lower()
