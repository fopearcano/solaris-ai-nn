"""Structural similarity: computed, fixture-overfit flag, low != failure."""

from __future__ import annotations

from solaris_ai_nn.developmental_replication import StructuralSimilarity


def _run(run_id, fixture, concepts, growth, contamination=0.1, boundary=0.7):
    return {"run_id": run_id, "fixture_live_replay": fixture,
            "developmental_profile": {
                "composite_growth": growth,
                "durable_prediction_improvement_score": growth,
                "structural_growth_status": "real_structural_growth"},
            "world_signature": {"concept_family_distribution": concepts,
                                "human_label_contamination_score": contamination,
                                "boundary_clarity_score": boundary},
            "source_diet": {"rf": 10, "vib": 8}}


def test_similarity_computed():
    a = _run("a", "live", {"rf": 3, "vib": 2}, 0.6)
    b = _run("b", "live", {"rf": 3, "vib": 2}, 0.58)
    result = StructuralSimilarity().compare(a, b)
    assert result.measured_dimensions >= 3
    assert 0.0 <= result.overall <= 1.0
    assert result.overall > 0.7


def test_high_similarity_can_flag_fixture_overfit():
    a = _run("a", "fixture", {"rf": 3, "vib": 2}, 0.6)
    b = _run("b", "fixture", {"rf": 3, "vib": 2}, 0.6)
    result = StructuralSimilarity().compare(a, b)
    assert result.overall >= 0.85
    assert any("fixture overfit" in c for c in result.caveats)


def test_low_similarity_not_failure():
    a = _run("a", "live", {"rf": 3, "vib": 2}, 0.6)
    c = _run("c", "live", {"txt": 5}, 0.2, contamination=0.8, boundary=0.3)
    result = StructuralSimilarity().compare(a, c)
    assert result.overall < 0.7
    # Low similarity must be framed as divergence/noise/insufficient, not
    # automatically failure.
    assert any("does not by itself mean failure" in cav
               for cav in result.caveats) or result.overall > 0.3
    assert "does not imply consciousness" in result.to_dict()["note"]
