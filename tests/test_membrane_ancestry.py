"""Membrane ancestry: concept/sign/cognition ancestry validates; missing detected."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.membrane_integration import (
    MembraneAncestryBuilder,
    SensoryImpressionLoader,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _membrane_integration_helpers import load_fixture, stage_pipeline  # noqa: E402


def _ancestry(tmp_path, include_bypass=False):
    state = stage_pipeline(str(tmp_path), include_bypass=include_bypass)
    impressions = SensoryImpressionLoader().load(state).impressions
    concept = ("bypass_concept.json" if include_bypass else "proto_concept.json")
    return MembraneAncestryBuilder().build(
        impressions=impressions,
        concept_records=load_fixture(concept)["records"],
        sign_records=load_fixture("sign_record.json")["records"],
        cognition_records=load_fixture("cognition_trace.json")["records"],
        membrane_available=True)


def test_concept_ancestry_validates(tmp_path):
    result = _ancestry(tmp_path)
    concepts = [c for c in result.chains if c.artifact_type == "proto_concept"]
    assert concepts
    assert concepts[0].has_impression_ancestry is True


def test_sign_ancestry_validates(tmp_path):
    result = _ancestry(tmp_path)
    signs = [c for c in result.chains if c.artifact_type == "private_sign"]
    assert signs
    assert signs[0].has_impression_ancestry is True


def test_cognition_ancestry_validates(tmp_path):
    result = _ancestry(tmp_path)
    traces = [c for c in result.chains
              if c.artifact_type == "cognition_trace"]
    assert traces
    assert traces[0].has_impression_ancestry is True
    assert traces[0].impression_ids  # links back to impressions


def test_missing_impression_ancestry_detected(tmp_path):
    result = _ancestry(tmp_path, include_bypass=True)
    # The bypass concept's source events are not in any impression.
    assert result.missing_ancestry >= 1
    assert any(c.fallback_raw_event for c in result.chains)
