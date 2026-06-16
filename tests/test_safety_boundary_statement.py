"""Safety boundary statement: items exist, missing evidence visible, fail blocks."""

from __future__ import annotations

from solaris_ai_nn.research_baseline import (
    SafetyBoundaryStatement,
    SafetyBoundaryStatus,
)


def test_boundary_items_exist():
    sbs = SafetyBoundaryStatement().build(safety_artifacts={"passed": True})
    d = sbs.to_dict()
    assert d["item_count"] >= 14
    items = {i["item"] for i in d["items"]}
    assert "no_real_world_actuation" in items
    assert "no_git_github_automation" in items
    assert "no_unsupported_consciousness_life_agency_claims" in items


def test_held_by_design_without_artifact():
    sbs = SafetyBoundaryStatement().build(safety_artifacts={})
    # No artifact supplied -> boundaries held by design (no capability exists).
    assert sbs.all_held is True
    assert all(i.status == SafetyBoundaryStatus.HELD_BY_DESIGN
               for i in sbs.items)


def test_missing_safety_evidence_visible():
    # Artifact present but not passing -> evidence missing (unverified).
    sbs = SafetyBoundaryStatement().build(safety_artifacts={"passed": False})
    assert sbs.evidence_missing
    assert SafetyBoundaryStatus.EVIDENCE_MISSING in {i.status for i in sbs.items}


def test_failed_boundary_blocks():
    sbs = SafetyBoundaryStatement().build(safety_artifacts={
        "passed": True, "failed_boundaries": ["no_real_world_actuation"]})
    assert sbs.fail_count >= 1
    assert sbs.all_held is False


def test_statement_is_mandatory_note():
    sbs = SafetyBoundaryStatement().build(safety_artifacts={"passed": True})
    assert "mandatory" in sbs.to_dict()["note"]
