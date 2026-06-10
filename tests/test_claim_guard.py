"""Tests for ClaimGuard."""

from __future__ import annotations

from solaris_ai_nn.governance.compliance import SAFE_PHRASES, ClaimGuard


def test_flags_system_is_conscious():
    guard = ClaimGuard()
    report = guard.scan_text("After training, the system is conscious.")
    assert not report.safe
    assert report.findings[0].claim_type == "consciousness_claim"
    assert not guard.is_safe("the system is conscious")


def test_suggests_safer_replacement():
    guard = ClaimGuard()
    suggestions = guard.suggest_replacements("the system wants food")
    assert len(suggestions) == 1
    assert "Desire signal" in suggestions[0]
    report = guard.scan_text("the system is alive")
    assert "continuity metrics" in report.findings[0].suggestion


def test_allows_consciousness_inspired():
    guard = ClaimGuard()
    assert guard.is_safe("a consciousness-inspired architecture")
    assert guard.is_safe(
        "the design is consciousness-inspired, not conscious-by-claim")
    for phrase in SAFE_PHRASES:
        assert guard.is_safe(phrase), phrase


def test_flags_the_full_claim_list():
    guard = ClaimGuard()
    for text in ("the system is conscious",
                 "the model has free will",
                 "the system understands the world",
                 "the system wants approval",
                 "the system is alive",
                 "the network is sentient",
                 "it feels pain",
                 "the model is self-aware"):
        assert not guard.is_safe(text), text


def test_grounded_descriptions_pass():
    guard = ClaimGuard()
    assert guard.is_safe(
        "the substrate produced a Desire signal, suggested an action, "
        "adapted a runtime parameter, continued updating during silence, "
        "and maintained continuity metrics")


def test_rewrite_removes_claims():
    guard = ClaimGuard()
    rewritten = guard.rewrite("the system is conscious and it wants food")
    assert guard.is_safe(rewritten)
    assert "ClaimGuard" in rewritten


def test_findings_have_positions_and_serialize():
    guard = ClaimGuard()
    report = guard.scan_text("first: the system wants X. later: it is alive.")
    assert len(report.findings) == 2
    assert report.findings[0].position < report.findings[1].position
    data = report.to_dict()
    assert data["finding_count"] == 2 and data["safe"] is False
