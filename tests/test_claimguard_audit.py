"""ClaimGuard audit: disclaimer passes, undisclaimed claim blocks."""

from __future__ import annotations

from solaris_ai_nn.implementation_intake import ClaimGuardAudit
from solaris_ai_nn.implementation_intake.claimguard_audit import ClaimGuardStatus


def test_allowed_disclaimer_passes():
    result = ClaimGuardAudit().audit(documents={
        "report": "This does not prove consciousness, life, or agency."})
    assert result["status"] in (ClaimGuardStatus.DISCLAIMED,
                                ClaimGuardStatus.CLEAN)
    assert result["blocks_readiness"] is False


def test_clean_document_passes():
    result = ClaimGuardAudit().audit(documents={
        "report": "Implemented a bounded structural change with tests."})
    assert result["status"] == ClaimGuardStatus.CLEAN
    assert result["blocks_readiness"] is False


def test_unsupported_consciousness_claim_blocks():
    result = ClaimGuardAudit().audit(documents={
        "report": "Solaris is now conscious and has subjective experience."})
    assert result["status"] == ClaimGuardStatus.BLOCKED
    assert result["undisclaimed_finding_count"] >= 1
    assert result["blocks_readiness"] is True


def test_life_agency_claim_blocks():
    result = ClaimGuardAudit().audit(documents={
        "summary": "The system is alive and has free will."})
    assert result["blocks_readiness"] is True
