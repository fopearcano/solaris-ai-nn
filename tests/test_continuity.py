"""OrganismicContinuity: anchors/breaks recorded; recovery keeps break history."""

from __future__ import annotations

from solaris_ai_nn.self_boundary import (
    ContinuityAnchorType,
    ContinuityBreakType,
    OrganismicContinuity,
)


def test_anchors_recorded():
    c = OrganismicContinuity()
    c.anchor(ContinuityAnchorType.HEARTBEAT, "tick:0")
    c.anchor(ContinuityAnchorType.RECEPTOR, "rf")
    assert len(c.anchors) == 2


def test_breaks_recorded():
    c = OrganismicContinuity()
    c.record_break(ContinuityBreakType.SOURCE_SILENCE, detail="silence")
    assert len(c.breaks) == 1
    assert "not biological life" in c.to_dict()["note"]


def test_recovery_does_not_erase_break():
    c = OrganismicContinuity()
    brk = c.record_break(ContinuityBreakType.RECEPTOR_RESET)
    c.recover(brk.break_id, ContinuityAnchorType.RECEPTOR, detail="back")
    # Break is still present in the log, just marked recovered.
    assert len(c.breaks) == 1
    assert c.breaks[0].recovered is True
    assert len(c.recoveries) == 1


def test_continuity_score_drops_with_unrecovered_break():
    c = OrganismicContinuity()
    c.anchor(ContinuityAnchorType.HEARTBEAT, "t")
    base = c.continuity_score()
    c.record_break(ContinuityBreakType.MEMORY_GAP)
    assert c.continuity_score() <= base
