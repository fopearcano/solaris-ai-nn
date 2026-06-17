"""Live sign generator: opaque, deterministic; label/gloss/secret never identity."""

from __future__ import annotations

from solaris_ai_nn.live_semiogenesis import (
    ConceptInputLoader,
    LivePrivateSignGenerator,
)


def _concepts():
    recs = [{"concept_id": "c1", "feature_signature": "machine_body:scalar:aa",
             "status": "born", "stability_score": 0.7, "recurrence_count": 5,
             "source_distribution": {"machine_body": 5},
             "modality_distribution": {"scalar": 5},
             "supporting_event_ids": ["e1"], "contamination_findings": []}]
    return ConceptInputLoader().from_records(recs, synthetic=True).eligible


def test_opaque_sign_generated():
    t = LivePrivateSignGenerator().generate_token("machine_body:scalar:aa")
    assert t.private_token.startswith("sig_live_")
    assert t.to_dict()["is_human_label"] is False


def test_deterministic_token():
    g = LivePrivateSignGenerator()
    a = g.generate_token("machine_body:scalar:aa")
    b = g.generate_token("machine_body:scalar:aa")
    assert a.private_token == b.private_token


def test_label_not_used_as_identity():
    res = LivePrivateSignGenerator().generate_for_concepts(
        _concepts(), requested_tokens={"c1": "the calm machine state"})
    cand = res.candidates[0]
    # The opaque token is kept; the label-derived request is refused.
    assert cand.private_token.startswith("sig_live_")
    assert "human_label_copy" in cand.contamination_findings


def test_secret_token_blocked():
    res = LivePrivateSignGenerator().generate_for_concepts(
        _concepts(), requested_tokens={"c1": "secret api_key=hunter2"})
    cand = res.candidates[0]
    assert "secret_marker" in cand.contamination_findings
    assert not cand.private_token.lower().startswith("secret")
