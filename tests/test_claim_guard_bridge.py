"""ClaimGuard bridge: scans text, blocking finding blocks readiness, disclaimers."""

from __future__ import annotations

from solaris_ai_nn.scientific_claims import ClaimGuardBridge


def test_reports_scanned():
    bridge = ClaimGuardBridge()
    results = bridge.scan_many({"abstract": "The system processes inputs.",
                                "registry": "Signs form under fixtures."})
    assert len(results) == 2
    assert all(r.claim_guard_available for r in results)


def test_blocked_finding_blocks_readiness():
    bridge = ClaimGuardBridge()
    # A consciousness assertion is flagged by ClaimGuard.
    result = bridge.scan("dossier", "The system is conscious and feels joy.")
    assert result.blocks_readiness is True
    assert bridge.any_blocked is True
    assert bridge.claimguard_block_count >= 1


def test_allowed_disclaimer_passes():
    bridge = ClaimGuardBridge()
    result = bridge.scan(
        "abstract",
        "This work makes no claim of consciousness or subjective experience.")
    assert result.safe is True
    assert result.blocks_readiness is False


def test_to_dict_shape():
    bridge = ClaimGuardBridge()
    bridge.scan("x", "ordinary text")
    d = bridge.to_dict()
    assert "claimguard_block_count" in d
    assert "never bypassed" in d["note"]
