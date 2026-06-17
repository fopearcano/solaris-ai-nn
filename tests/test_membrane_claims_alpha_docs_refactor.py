"""Claims/Alpha/docs refactor: evidence typing, alpha status, docs disclaimers."""

from __future__ import annotations

import json
import os
import sys

from solaris_ai_nn.alpha_system.alpha_orchestrator import AlphaResearchOrchestrator
from solaris_ai_nn.membrane_integration import (
    MembraneIntegrationRuntime,
    ScientificClaimsMembraneAdapter,
    SensoryImpressionLoader,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _membrane_integration_helpers import stage_pipeline  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_claims_evidence_typing(tmp_path):
    state = stage_pipeline(str(tmp_path))
    load = SensoryImpressionLoader().load(state)
    r = ScientificClaimsMembraneAdapter().run(state, load, [])
    cats = r.data["evidence_categories"]
    assert "raw_event_evidence" in cats
    assert "membrane_filtered_sensory_impression_evidence" in cats
    assert "downstream_concept_sign_cognition_evidence_with_ancestry" in cats
    assert r.data["raw_event_supports_birth_claims"] is False


def test_alpha_membrane_integration_status_after_run(tmp_path):
    state = stage_pipeline(str(tmp_path))
    MembraneIntegrationRuntime(
        state_dir=state, profile="fixture_integration_v0").run()
    alpha = AlphaResearchOrchestrator()
    status = alpha.membrane_integration_status(live_state_dir=state)
    assert status["membrane_integration_available"] is True
    assert status["impression_count"] == 4
    assert status["learns"] is False
    assert status["controls_feeders"] is False


def test_alpha_status_absent_without_integration(tmp_path):
    alpha = AlphaResearchOrchestrator()
    status = alpha.membrane_integration_status(live_state_dir=str(tmp_path))
    assert status["membrane_integration_available"] is False


def test_docs_state_raw_events_not_perception():
    for rel in ("README.md", os.path.join("docs", "ARCHITECTURE.md"),
                os.path.join("docs", "RESEARCH_NOTES.md")):
        text = open(os.path.join(_ROOT, rel)).read().lower()
        assert "raw events are not perception" in text, rel


def test_docs_mention_integration_commands():
    readme = open(os.path.join(_ROOT, "README.md")).read()
    for cmd in ("membrane-integrate", "membrane-audit", "membrane-bypass",
                "membrane-ancestry", "membrane-contracts"):
        assert cmd in readme, cmd
