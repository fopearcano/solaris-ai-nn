"""SelfBoundaryState: zones exist; uncertainty allowed; no subjective self."""

from __future__ import annotations

from solaris_ai_nn.self_boundary import (
    BoundaryConfidence,
    BoundaryZone,
    SelfBoundaryState,
)


def test_boundary_zones_exist():
    assert len(BoundaryZone.ALL) == 11
    for z in ("internal_state", "receptor_body", "external_feeder",
              "external_world_source", "simulation", "counterfactual",
              "unknown"):
        assert z in BoundaryZone.ALL


def test_uncertainty_allowed():
    state = SelfBoundaryState()
    ev = state.add(BoundaryZone.UNKNOWN, "blob", confidence=0.1)
    assert ev.uncertain is True
    assert ev.confidence_band == BoundaryConfidence.LOW
    assert state.unknown_count() == 1


def test_unknown_zone_fallback():
    state = SelfBoundaryState()
    ev = state.add("not_a_real_zone", "x", confidence=0.5)
    assert ev.zone == BoundaryZone.UNKNOWN


def test_no_subjective_self_claims():
    state = SelfBoundaryState()
    state.add(BoundaryZone.RECEPTOR_BODY, "r1", 0.8)
    note = state.to_dict()["note"].lower()
    assert "not subjective selfhood" in note
    assert "not personhood" in note


def test_confidence_score_and_distribution():
    state = SelfBoundaryState()
    state.add(BoundaryZone.RECEPTOR_BODY, "r1", 0.8)
    state.add(BoundaryZone.EXTERNAL_WORLD_SOURCE, "s1", 0.6)
    assert 0.0 <= state.confidence_score() <= 1.0
    dist = state.zone_distribution()
    assert dist[BoundaryZone.RECEPTOR_BODY] == 1
    assert dist[BoundaryZone.EXTERNAL_WORLD_SOURCE] == 1
