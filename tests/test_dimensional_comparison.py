"""Tests for the dimensional comparator."""

from __future__ import annotations

from solaris_ai_nn.ego.dimensional_comparison import (
    DIMENSION_VALUES,
    Dimension,
    DimensionalComparator,
    DimensionalFrame,
)

STREAM = {"source": "stream", "kind": "stream_line"}
COUNTERFACTUAL = {"source": "counterfactual", "kind": "dream_trace"}
GRID_ACTION = {"source": "grid_world", "kind": "simulated_action",
               "label": "move_north"}
OPERATOR = {"source": "operator", "kind": "approval"}


def test_frames_classify_events():
    comparator = DimensionalComparator()
    stream = comparator.classify_event(STREAM)
    assert stream.scope == "stream_input"
    assert stream.evidence == "real_observed"
    assert stream.certainty == "high"
    cf = comparator.classify_event(COUNTERFACTUAL)
    assert cf.evidence == "counterfactual"
    assert cf.temporal == "replay_offline"
    grid = comparator.classify_event(GRID_ACTION)
    assert grid.scope == "grid_world"
    assert grid.evidence == "simulated"
    operator = comparator.classify_event(OPERATOR)
    assert operator.scope == "external_operator"
    assert operator.authority == "governance_approval"
    # Every frame names its evidence.
    assert stream.evidence_refs and cf.evidence_refs


def test_distance_deterministic():
    comparator = DimensionalComparator()
    a = comparator.classify_event(STREAM)
    b = comparator.classify_event(COUNTERFACTUAL)
    d1 = comparator.distance(a, b)
    d2 = comparator.distance(a, b)
    assert d1 == d2
    assert 0.0 < d1 <= 1.0
    assert comparator.distance(a, a) == 0.0
    # Symmetric.
    assert comparator.distance(b, a) == d1


def test_difference_explanation_generated():
    comparator = DimensionalComparator()
    comparison = comparator.compare(STREAM, COUNTERFACTUAL)
    assert comparison.explanation.startswith("The frames differ on")
    assert "evidence" in comparison.differing_dimensions
    assert "not experiential" in comparison.explanation
    same = comparator.compare(STREAM, dict(STREAM))
    assert "agree on all six dimensions" in same.explanation
    assert same.distance == 0.0


def test_classify_context_modes():
    comparator = DimensionalComparator()
    dreaming = comparator.classify_context({"latent_mode": "dream"})
    assert dreaming.temporal == "replay_offline"
    emergency = comparator.classify_context({"emergency": True})
    assert emergency.authority == "forbidden"
    assert emergency.risk == "prohibited"
    embodied = comparator.classify_context({"embodied": True,
                                            "health_level": "ok"})
    assert embodied.scope == "grid_world"
    assert embodied.evidence == "simulated"


def test_dimension_value_inventories():
    assert len(Dimension.ALL) == 6
    for dimension in Dimension.ALL:
        assert len(DIMENSION_VALUES[dimension]) >= 4
    assert "counterfactual" in DIMENSION_VALUES[Dimension.EVIDENCE]
    assert "prohibited" in DIMENSION_VALUES[Dimension.RISK]
    frame = DimensionalFrame()
    for dimension in Dimension.ALL:
        assert isinstance(frame.value(dimension), str)
