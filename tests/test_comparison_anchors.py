"""Comparison anchors: created, missing anchor limitation, control preserved."""

from __future__ import annotations

from solaris_ai_nn.research_baseline import AnchorKind, ComparisonAnchorSet


def test_anchors_created():
    anc = ComparisonAnchorSet().build(
        parent_baseline_id="b1", previous_validated_id="b0",
        available_anchors={AnchorKind.PASSIVE_PARSER_BASELINE: "ctrl_pp"}
    ).to_dict()
    assert anc["comparison_anchor_count"] == len(
        [k for k in AnchorKind.ALL if k != AnchorKind.UNKNOWN])
    assert anc["available_anchor_count"] >= 3


def test_missing_anchor_is_limitation():
    anc = ComparisonAnchorSet().build().to_dict()
    # No anchors supplied -> every anchor is a missing-anchor limitation.
    assert anc["missing_anchor_limitations"]
    assert any("missing comparison anchor" in m
               for m in anc["missing_anchor_limitations"])


def test_control_anchor_preserved_even_if_weak():
    aset = ComparisonAnchorSet().build()
    control = next(a for a in aset.anchors
                   if a.kind == AnchorKind.PASSIVE_PARSER_BASELINE)
    # Control anchors are kept available even if weak / not yet recorded.
    assert "kept available even if weak" in control.detail


def test_parent_anchor_recorded():
    aset = ComparisonAnchorSet().build(parent_baseline_id="b1")
    parent = next(a for a in aset.anchors
                  if a.kind == AnchorKind.PARENT_BASELINE)
    assert parent.available is True
    assert parent.baseline_id == "b1"
