"""Membrane <-> Alpha / Research Cycle / Scientific Claims integration."""

from __future__ import annotations

import json
import os
import shutil

from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.environmental_membrane import EnvironmentalMembraneRuntime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FIXTURES = os.path.join(_ROOT, "examples", "environmental_membrane")


def _run(tmp_path):
    state = str(tmp_path)
    for sub in ("governance", "feeders", "inbox"):
        os.makedirs(os.path.join(state, sub), exist_ok=True)
    json.dump(approved_governance(), open(os.path.join(
        state, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state, "feeders", "FEEDER_REGISTRY.json"), "w"))
    shutil.copy(os.path.join(_FIXTURES, "sample_validated_events.jsonl"),
                os.path.join(state, "inbox", "events.jsonl"))
    rt = EnvironmentalMembraneRuntime(state_dir=state, require_governance=True)
    rt.run()
    return state, rt


def test_alpha_exposes_membrane_status(tmp_path):
    from solaris_ai_nn.alpha_system.alpha_orchestrator import (
        AlphaResearchOrchestrator,
    )

    state, rt = _run(tmp_path)
    o = AlphaResearchOrchestrator(state_dir=str(tmp_path) + "_alpha")
    status = o.environmental_membrane_status(live_state_dir=state)
    assert status["membrane_enabled"] is True
    assert status["controls_feeders"] is False
    assert "membrane_impression_count" in status


def test_research_cycle_receives_membrane_evidence(tmp_path):
    state, rt = _run(tmp_path)
    update = rt.research_cycle_update()
    assert update["membrane_evidence_recorded"] is True
    assert "sensory impressions" in update["next_action"].lower()
    assert update["operational_only"] is True


def test_scientific_claims_distinguish_raw_vs_impression(tmp_path):
    state, rt = _run(tmp_path)
    claims = rt.scientific_claims_update()
    assert claims["evidence_kind"] == "operational_membrane_filtered_impression"
    assert claims["distinguishes_raw_from_impression"] is True
    assert claims["blocks_consciousness_life_agency_interpretation"] is True
