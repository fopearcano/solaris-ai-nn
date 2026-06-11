"""Tests for identity anchors and continuity scoring."""

from __future__ import annotations

from solaris_ai_nn.ego.identity import (
    ANCHOR_NAMES,
    IdentityAnchor,
    IdentityState,
)

ANCHORS = {"run_id": "run-1", "session_id": "s1",
           "substrate_identity": "esn", "state_path": "/state/x",
           "inner_map_signature": "map-v1"}


def test_identity_anchors_serialize():
    identity = IdentityState()
    identity.update(ANCHORS)
    data = identity.to_dict()
    assert data["anchors"]["run_id"]["value"] == "run-1"
    assert data["anchors"]["run_id"]["source"] == "lifecycle"
    assert "personhood" in data["note"] or "not personhood" in data["note"]
    anchor = IdentityAnchor(name="run_id", value="run-1")
    assert anchor.matches(IdentityAnchor(name="run_id", value="run-1"))
    assert not anchor.matches(IdentityAnchor(name="run_id", value="run-2"))
    assert set(ANCHORS) <= set(ANCHOR_NAMES)


def test_continuity_score_computed():
    identity = IdentityState()
    first = identity.update(ANCHORS)
    assert first.score == 1.0  # no previous anchors: asserted, qualified
    second = identity.update(dict(ANCHORS))
    assert second.score == 1.0
    assert identity.continuity_score == 1.0
    assert identity.mismatch_count == 0
    assert identity.identity_confidence == 1.0


def test_mismatch_creates_warning():
    identity = IdentityState()
    identity.update(ANCHORS)
    result = identity.update(dict(ANCHORS, run_id="run-OTHER"))
    assert "run_id" in result.mismatched
    assert result.score < 1.0
    assert any("mismatch" in w for w in result.warnings)
    assert identity.mismatch_count == 1
    assert identity.identity_warnings  # persisted as unresolved


def test_session_scoped_anchors_rotate_quietly():
    identity = IdentityState()
    identity.update(ANCHORS)
    result = identity.update(dict(ANCHORS, session_id="s2"))
    assert "session_id" in result.mismatched
    # Expected rotation: lowers the score slightly, no warning, no
    # persistent mismatch count.
    assert not any("mismatch" in w for w in result.warnings)
    assert identity.mismatch_count == 0


def test_restart_gap_and_checkpoint_flags():
    identity = IdentityState()
    identity.update(ANCHORS)
    result = identity.update(dict(ANCHORS, restart_gap_detected=True,
                                  restored_from_checkpoint=True))
    assert identity.restart_gap_detected is True
    assert identity.restored_from_checkpoint is True
    assert any("gap" in w for w in result.warnings)
    assert result.score < 1.0
