"""Evidence mapping: supports/contradicts/falsifies, missing, many-to-many."""

from __future__ import annotations

from solaris_ai_nn.scientific_claims import (
    EvidenceMap,
    EvidenceRole,
    MappedEvidence,
)


def test_supports_contradicts_falsifies():
    em = EvidenceMap()
    em.map_evidence("c1", MappedEvidence("e1", "semiogenesis",
                                         EvidenceRole.SUPPORTS))
    em.map_evidence("c1", MappedEvidence("e2", "replication_falsification",
                                         EvidenceRole.CONTRADICTS))
    em.map_evidence("c1", MappedEvidence("e3", "replication_falsification",
                                         EvidenceRole.FALSIFIES))
    assert em.has_support("c1")
    assert em.has_contradiction("c1")
    assert "e2" in em.against_refs("c1")
    assert "e3" in em.against_refs("c1")


def test_missing_evidence_explicit():
    em = EvidenceMap()
    em.map_evidence("c1", MappedEvidence("e_missing", "live_field",
                                         EvidenceRole.MISSING))
    assert "e_missing" in em.missing_refs("c1")
    assert em.to_dict()["missing_count"] == 1


def test_many_to_many():
    em = EvidenceMap()
    em.map_evidence("c1", MappedEvidence("e1", "cognition",
                                         EvidenceRole.SUPPORTS))
    em.map_evidence("c2", MappedEvidence("e1", "cognition",
                                         EvidenceRole.WEAKLY_SUPPORTS))
    em.map_evidence("c1", MappedEvidence("e2", "self_boundary",
                                         EvidenceRole.SUPPORTS))
    assert em.evidence_mapping_count == 3
    assert len(em.for_claim("c1")) == 2
    assert len(em.for_claim("c2")) == 1


def test_unknown_role_and_source_normalized():
    ev = MappedEvidence("e1", "not_a_source", "not_a_role")
    assert ev.role == EvidenceRole.INCONCLUSIVE
    assert ev.source == "operator_notes"
