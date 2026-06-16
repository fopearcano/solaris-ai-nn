"""Limitations builder: generated, specific, mandatory, linked to claims."""

from __future__ import annotations

from solaris_ai_nn.scientific_claims import (
    LimitationCategory,
    LimitationsBuilder,
)


def test_limitations_generated_and_mandatory_present():
    lims = LimitationsBuilder().build({}, claim_refs=["c1"])
    cats = {l.category for l in lims}
    for mandatory in LimitationCategory.MANDATORY:
        assert mandatory in cats


def test_limitations_specific_and_linked_to_claims():
    lims = LimitationsBuilder().build(
        {"missing_live_data": True, "fixture_overfit_risk": True},
        claim_refs=["c1", "c2"])
    by_cat = {l.category: l for l in lims}
    assert LimitationCategory.MISSING_LIVE_DATA in by_cat
    assert LimitationCategory.FIXTURE_DEPENDENCE in by_cat
    # Each limitation is linked to the claims it constrains.
    assert all(l.claim_refs == ["c1", "c2"] for l in lims)
    # Specific (non-empty) text.
    assert all(l.text.strip() for l in lims)


def test_summary_counts_mandatory():
    lims = LimitationsBuilder().build({}, claim_refs=[])
    summary = LimitationsBuilder.summary(lims)
    assert summary["mandatory_count"] == len(LimitationCategory.MANDATORY)
    assert summary["limitation_count"] >= summary["mandatory_count"]
