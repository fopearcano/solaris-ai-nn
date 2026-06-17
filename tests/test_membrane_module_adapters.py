"""Module adapters: birth/observation/ontogenesis/semiogenesis/cognition bridges."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.membrane_integration import (
    LiveBirthMembraneAdapter,
    LiveCognitionMembraneAdapter,
    LiveObservationMembraneAdapter,
    LiveOntogenesisMembraneAdapter,
    LiveSemiogenesisMembraneAdapter,
    MembraneAncestryBuilder,
    ScientificClaimsMembraneAdapter,
    SensoryImpressionLoader,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _membrane_integration_helpers import load_fixture, stage_pipeline  # noqa: E402


def _load(tmp_path, include_bypass=False):
    state = stage_pipeline(str(tmp_path), include_bypass=include_bypass)
    return state, SensoryImpressionLoader().load(state)


def _ancestry(state, load, include_bypass=False):
    concept = "bypass_concept.json" if include_bypass else "proto_concept.json"
    return MembraneAncestryBuilder().build(
        impressions=load.impressions,
        concept_records=load_fixture(concept)["records"],
        sign_records=load_fixture("sign_record.json")["records"],
        cognition_records=load_fixture("cognition_trace.json")["records"],
        membrane_available=True)


def test_birth_adapter_reports_handoff(tmp_path):
    state, load = _load(tmp_path)
    r = LiveBirthMembraneAdapter().run(state, load)
    assert r.data["membrane_available"] is True
    assert r.data["live_birth_bypasses_membrane"] is False


def test_observation_adapter_distinguishes_diets(tmp_path):
    state, load = _load(tmp_path)
    r = LiveObservationMembraneAdapter().run(state, load)
    assert r.used_impressions is True
    assert r.data["distinguishes_event_and_impression_diet"] is True
    assert r.data["impression_diet"]


def test_ontogenesis_adapter_uses_impressions(tmp_path):
    state, load = _load(tmp_path)
    r = LiveOntogenesisMembraneAdapter().run(state, load)
    assert r.used_impressions is True
    assert r.raw_fallback is False
    assert r.data["concept_birth_requires_impressions"] is True


def test_ontogenesis_adapter_raw_fallback_loud_and_strict_block(tmp_path):
    # No membrane staged -> no impressions -> loud fallback / strict block.
    empty = str(tmp_path)
    load = SensoryImpressionLoader().load(empty)
    soft = LiveOntogenesisMembraneAdapter().run(empty, load, strict=False)
    assert soft.raw_fallback is True
    assert soft.status == "fallback_used"
    assert "RAW FALLBACK" in soft.detail
    strict = LiveOntogenesisMembraneAdapter().run(empty, load, strict=True)
    assert strict.status == "blocked"


def test_semiogenesis_and_cognition_adapters_check_ancestry(tmp_path):
    state, load = _load(tmp_path)
    anc = _ancestry(state, load)
    semio = LiveSemiogenesisMembraneAdapter().run(state, anc)
    cog = LiveCognitionMembraneAdapter().run(state, anc)
    assert semio.data["signs_with_impression_ancestry"] >= 1
    assert cog.data["traces_with_impression_ancestry"] >= 1
    assert cog.data["distinguishes_event_vs_impression_prediction"] is True


def test_claims_adapter_types_evidence(tmp_path):
    state, load = _load(tmp_path)
    r = ScientificClaimsMembraneAdapter().run(state, load, [])
    assert "raw_event_evidence" in r.data["evidence_categories"]
    assert r.data["raw_event_supports_birth_claims"] is False
    assert r.data["mentions_membrane_status"] is True
