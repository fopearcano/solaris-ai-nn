"""Capability map: statuses computed, refs included, no overclaim w/o evidence."""

from __future__ import annotations

from solaris_ai_nn.research_baseline import BaselineCapabilityMap, CapabilityStatus


def test_capability_statuses_computed():
    cap = BaselineCapabilityMap().build(evidence={}).to_dict()
    assert cap["capability_count"] == 22
    # All stack packages are importable -> available (not missing).
    statuses = {r["status"] for r in cap["records"].values()}
    assert CapabilityStatus.AVAILABLE in statuses


def test_validated_includes_evidence_refs():
    cap = BaselineCapabilityMap().build(evidence={
        "plural_sensorium": {"status": "validated",
                             "evidence_refs": ["replication:ok"],
                             "limitations": ["fixture-weighted"]}}).to_dict()
    rec = cap["records"]["plural_sensorium"]
    assert rec["status"] == CapabilityStatus.VALIDATED
    assert rec["evidence_refs"] == ["replication:ok"]
    assert rec["limitations"]
    assert cap["validated_capability_count"] >= 1


def test_no_overclaim_without_evidence():
    # Declared validated but no evidence refs -> downgraded to available.
    cap = BaselineCapabilityMap().build(evidence={
        "semiogenesis": {"status": "validated", "evidence_refs": []}}).to_dict()
    rec = cap["records"]["semiogenesis"]
    assert rec["status"] == CapabilityStatus.AVAILABLE
    assert any("downgraded" in l for l in rec["limitations"])


def test_means_implemented_not_intelligence():
    cap = BaselineCapabilityMap().build(evidence={}).to_dict()
    assert "not intelligence" in cap["note"]
    for rec in cap["records"].values():
        assert rec["means_implemented_not_intelligence"] is True
