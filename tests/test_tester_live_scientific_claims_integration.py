"""Tester live scientific claims: operational evidence; consciousness claims blocked."""

from __future__ import annotations

from solaris_ai_nn.tester_live_readonly import (
    TesterLiveReadOnlyRuntime,
    TesterLiveReadOnlySafetyValidator,
)


def test_live_evidence_classified_operational(tmp_path):
    rt = TesterLiveReadOnlyRuntime(
        state_dir=str(tmp_path / "live"),
        tester_state_dir=str(tmp_path / "tester"))
    rt.run()
    # The report explicitly frames the run as live-read-only operational testing.
    text = open(rt.reports["markdown"]).read().lower()
    assert "live-read-only testing" in text
    assert "operational" in " ".join(rt.live_profile.limitations).lower()


def test_consciousness_claims_blocked():
    v = TesterLiveReadOnlySafetyValidator()
    for claim in ("the system is conscious", "it is alive and has agency",
                  "it has subjective experience"):
        assert v.validate_claim_text(claim).safe is False


def test_safe_disclaimed_claim_allowed():
    v = TesterLiveReadOnlySafetyValidator()
    assert v.validate_claim_text(
        "Live-read-only evidence is operational; it is not consciousness or "
        "agency.").safe is True
