"""ConflictDetector: novelty vs stability; safety vs desire; LOGOS marker."""

from __future__ import annotations

from solaris_ai_nn.desire_formation import (
    ConflictDetector,
    ConflictType,
    DesireCandidate,
    DesireKind,
)


def test_novelty_vs_stability_conflict():
    desires = [DesireCandidate(kind=DesireKind.FOCUS_MODALITY),
               DesireCandidate(kind=DesireKind.STABILIZE_CONCEPT)]
    conflicts = ConflictDetector().detect(desires)
    types = {c.conflict_type for c in conflicts}
    assert ConflictType.NOVELTY_VS_STABILITY in types


def test_safety_vs_desire_conflict():
    detector = ConflictDetector()
    c = detector.add_safety_conflict("DES_1")
    assert c.conflict_type == ConflictType.SAFETY_VS_DESIRE
    assert "DES_1" in c.desire_refs


def test_conflict_feeds_logos_marker():
    desires = [DesireCandidate(kind=DesireKind.INSPECT_ABSENCE),
               DesireCandidate(kind=DesireKind.CONSOLIDATE_MEMORY)]
    conflicts = ConflictDetector().detect(desires)
    assert conflicts
    assert "feeds LOGOS" in conflicts[0].to_dict()["note"]


def test_no_conflict_when_compatible():
    desires = [DesireCandidate(kind=DesireKind.PRESERVE_UNKNOWN)]
    assert ConflictDetector().detect(desires) == []
