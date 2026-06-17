"""Live sign input: sign memory loads, contaminated excluded, rejected preserved."""

from __future__ import annotations

from solaris_ai_nn.live_cognition import SignInputLoader


def _rec(sid, status, contamination=None):
    return {"sign_id": sid, "private_token": f"sig_live_{sid}", "status": status,
            "linked_concept_ids": ["c1"], "utility_score": 0.7,
            "source_distribution": {"machine_body": 5},
            "supporting_refs": ["c1"], "contradicting_refs": [],
            "contamination_findings": contamination or []}


def test_sign_memory_loads():
    recs = [_rec("s1", "born"), _rec("s2", "stable_candidate")]
    result = SignInputLoader().from_records(recs, synthetic=True)
    assert len(result.eligible) == 2


def test_contaminated_signs_excluded():
    recs = [_rec("s1", "born"),
            _rec("s2", "born", contamination=["operator_pulse_dominance"])]
    result = SignInputLoader().from_records(recs, synthetic=True)
    eligible_ids = {s.sign_id for s in result.eligible}
    assert "s1" in eligible_ids
    assert "s2" not in eligible_ids


def test_rejected_signs_preserved_as_counterevidence():
    recs = [_rec("s1", "born"), _rec("s2", "rejected")]
    result = SignInputLoader().from_records(recs, synthetic=True)
    counter_ids = {s.sign_id for s in result.counterevidence}
    assert "s2" in counter_ids
    assert any(s.sign_id == "s2" for s in result.signs)


def test_missing_sign_memory(tmp_path):
    result = SignInputLoader().load(str(tmp_path))
    assert result.status == "missing_sign_memory"
    assert not result.eligible
