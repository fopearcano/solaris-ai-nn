"""Live concept input: memory loads, contaminated excluded, rejected preserved."""

from __future__ import annotations

from solaris_ai_nn.live_semiogenesis import ConceptInputLoader


def _rec(cid, status, contamination=None):
    return {"concept_id": cid, "feature_signature": f"sig:{cid}",
            "status": status, "stability_score": 0.7, "recurrence_count": 5,
            "source_distribution": {"machine_body": 5},
            "modality_distribution": {"scalar": 5},
            "supporting_event_ids": ["e1", "e2"],
            "contamination_findings": contamination or []}


def test_concept_memory_loads():
    recs = [_rec("c1", "born"), _rec("c2", "stable_candidate")]
    result = ConceptInputLoader().from_records(recs, synthetic=True)
    assert len(result.eligible) == 2


def test_contaminated_concepts_excluded():
    recs = [_rec("c1", "born"),
            _rec("c2", "born", contamination=["operator_pulse_dominance"])]
    result = ConceptInputLoader().from_records(recs, synthetic=True)
    eligible_ids = {c.concept_id for c in result.eligible}
    assert "c1" in eligible_ids
    assert "c2" not in eligible_ids


def test_rejected_concepts_preserved_as_counterevidence():
    recs = [_rec("c1", "born"), _rec("c2", "rejected")]
    result = ConceptInputLoader().from_records(recs, synthetic=True)
    counter_ids = {c.concept_id for c in result.counterevidence}
    assert "c2" in counter_ids
    # still visible in the full concept list
    assert any(c.concept_id == "c2" for c in result.concepts)


def test_missing_concept_memory(tmp_path):
    result = ConceptInputLoader().load(str(tmp_path))
    assert result.status == "missing_concept_memory"
    assert not result.eligible
