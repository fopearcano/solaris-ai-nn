"""Reviewer pack: generated, counterevidence included, disclaimers present."""

from __future__ import annotations

from solaris_ai_nn.independent_review import ReviewerPackBuilder


def _build(**overrides):
    kwargs = dict(
        claim_registry={"claims": [
            {"claim_id": "c1", "text": "Signs form.", "category": "sensorium_claim",
             "status": "supported", "evidence_refs": ["e1"],
             "counterevidence_refs": []},
            {"claim_id": "c2", "text": "Binding everywhere.",
             "category": "sensorium_claim", "status": "unsupported",
             "evidence_refs": [], "counterevidence_refs": []}]},
        counterevidence={"records": [
            {"counter_type": "fixture_overfit", "detail": "maybe overfit"}]},
        limitations={"limitations": [{"text": "no replication"}]},
        manifest={"artifacts": [{"category": "claim_registry"}]},
        challenges={"steps": [
            {"challenge_type": "fixture_demo_reproduction", "status": "available",
             "command": "python examples/run_minimal_field_organism_demo.py",
             "expected": {"expected_artifact": "trace"}}]},
        questions={"questions": [{"text": "Could passive parsing explain this?"}]})
    kwargs.update(overrides)
    return ReviewerPackBuilder().build(**kwargs)


def test_pack_generated():
    pack = _build().to_dict()
    assert pack["reviewer_pack_section_count"] > 0
    assert pack["published"] is False and pack["uploaded"] is False
    assert "what_is_being_claimed" in pack["sections"]


def test_counterevidence_included():
    sec = _build().sections
    assert sec["counterevidence_table"]
    assert sec["counterevidence_table"][0]["counter_type"] == "fixture_overfit"


def test_forbidden_claim_disclaimers_included():
    sec = _build().sections
    assert "consciousness" in " ".join(sec["what_is_not_being_claimed"])
    assert "makes no claim of consciousness" in sec["disclaimer"]


def test_unsupported_claims_listed_separately():
    sec = _build().sections
    assert any("Binding everywhere" in c for c in sec["claims_not_reviewable"])


def test_sanitizer_block_flag_carried():
    pack = _build(sanitizer_blocked=True).to_dict()
    assert pack["sanitizer_blocked"] is True
