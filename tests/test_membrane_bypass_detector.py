"""Membrane bypass detector: raw path, missing ancestry, propagation, strict block."""

from __future__ import annotations

from solaris_ai_nn.membrane_integration import (
    MembraneBypassDetector,
    MembraneBypassSeverity,
)


class _Ancestry:
    def __init__(self, *, membrane_available=True, missing=0, contaminated=0,
                 fallback=0):
        self.membrane_available = membrane_available
        self.missing_ancestry = missing
        self.contaminated_ancestry = contaminated
        self.chains = [type("C", (), {"fallback_raw_event": True})()
                       for _ in range(fallback)]


def test_membrane_present_no_impressions_detected():
    findings = MembraneBypassDetector().detect(
        impressions_present=False, membrane_present=True,
        ancestry=_Ancestry(), contracts=[], strict=False)
    assert any(f.finding == "membrane_present_no_impressions" for f in findings)


def test_missing_ancestry_detected():
    findings = MembraneBypassDetector().detect(
        impressions_present=True, membrane_present=True,
        ancestry=_Ancestry(missing=2), contracts=[], strict=False)
    assert any(f.finding == "missing_impression_ancestry" for f in findings)


def test_contamination_propagation_flagged():
    findings = MembraneBypassDetector().detect(
        impressions_present=True, membrane_present=True,
        ancestry=_Ancestry(contaminated=1), contracts=[], strict=False)
    assert any(f.finding == "contamination_propagated_ancestry"
               for f in findings)


def test_raw_event_fallback_and_unmarked_critical():
    findings = MembraneBypassDetector().detect(
        impressions_present=True, membrane_present=True,
        ancestry=_Ancestry(fallback=1), contracts=[], strict=False,
        raw_fallback_marked=False)
    names = {f.finding for f in findings}
    assert "raw_event_fallback_used" in names
    assert "raw_fallback_not_marked" in names


def test_strict_critical_bypass_blocks():
    findings = MembraneBypassDetector().detect(
        impressions_present=True, membrane_present=True,
        ancestry=_Ancestry(missing=1, fallback=1), contracts=[], strict=True)
    # Missing ancestry is critical, raw fallback is a blocker in strict mode.
    assert MembraneBypassDetector.has_blocking(findings)
    summ = MembraneBypassDetector.summary(findings)
    assert summ["critical_bypass_count"] >= 1
    assert summ["worst_severity"] == MembraneBypassSeverity.CRITICAL


def test_no_membrane_no_ancestry_bypass():
    # When membrane is unavailable, missing ancestry is not flagged as a bypass.
    findings = MembraneBypassDetector().detect(
        impressions_present=False, membrane_present=False,
        ancestry=_Ancestry(membrane_available=False, missing=3),
        contracts=[], strict=True)
    assert not any(f.finding == "missing_impression_ancestry" for f in findings)
