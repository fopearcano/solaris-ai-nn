"""Tester scientific claims: fixture-only evidence; consciousness interpretation blocked."""

from __future__ import annotations

from solaris_ai_nn.tester_fixture_spine import TesterFixtureDemoRuntime


def test_evidence_classified_fixture_only(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt.run()
    cs = rt.stage_summaries["claim_safety"]
    assert cs["evidence_kind"] == "fixture_only_operational_evidence"
    assert cs["raw_event_supports_claims"] is False


def test_consciousness_interpretation_blocked(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt.run()
    cs = rt.stage_summaries["claim_safety"]
    assert cs["blocks_consciousness_life_agency_interpretation"] is True
    assert cs["claims_safe"] is True


def test_claim_scan_runs_with_or_without_claimguard(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt.run()
    cs = rt.stage_summaries["claim_safety"]
    assert "claimguard_available" in cs
    assert cs["claims_safe"] is True
