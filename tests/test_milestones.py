"""Tests for milestones."""

from __future__ import annotations

import pytest

from solaris_ai_nn.developmental.milestones import (
    Milestone,
    MilestoneDetector,
    MilestoneType,
)


def test_milestone_detected():
    detector = MilestoneDetector()
    new = detector.detect({"runtime_hours": 25.0,
                           "stable_habit_count": 1})
    types = {m.type for m in new}
    assert MilestoneType.FIRST_24H_SURVIVAL in types
    assert MilestoneType.FIRST_STABLE_HABIT in types
    # Each first fires once.
    again = detector.detect({"runtime_hours": 30.0,
                             "stable_habit_count": 5})
    assert not again
    assert detector.registry.has(MilestoneType.FIRST_24H_SURVIVAL)


def test_evidence_refs_required():
    with pytest.raises(ValueError, match="evidence"):
        Milestone(type=MilestoneType.FIRST_STABLE_HABIT,
                  description="x", evidence_refs=[])
    with pytest.raises(ValueError, match="unknown milestone"):
        Milestone(type="first_enlightenment", evidence_refs=["e"])
    detector = MilestoneDetector()
    for milestone in detector.detect({"mysterium_pressure": 0.9}):
        assert milestone.evidence_refs


def test_milestone_becomes_fossil_candidate():
    detector = MilestoneDetector()
    new = detector.detect({"consolidation_count": 1})
    assert new
    assert all(m.fossil_candidate for m in new)
    assert detector.registry.fossil_candidates() == \
        detector.registry.milestones


def test_language_like_structure_is_internal_only():
    detector = MilestoneDetector()
    new = detector.detect({"meaning_atom_count": 60})
    milestone = [m for m in new if m.type
                 == MilestoneType.FIRST_LANGUAGE_LIKE_STRUCTURE][0]
    assert "not" in milestone.description
    assert "human-level language" in milestone.description


def test_simulated_flag_carried():
    detector = MilestoneDetector()
    simulated = detector.detect({"runtime_hours": 25.0},
                                simulated=True)[0]
    assert simulated.simulated is True
    assert len(MilestoneType.ALL) == 30
