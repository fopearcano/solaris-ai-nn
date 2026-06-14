"""NullModel: random shuffle runs; static model runs; small sample inconclusive."""

from __future__ import annotations

import pytest

from solaris_ai_nn.research_lab import NullModel, NullModelType


def test_random_shuffle_runs():
    nm = NullModel(NullModelType.RANDOM_METRIC_SHUFFLE)
    result = nm.evaluate([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.9, 1.1, 1.4])
    assert result.inconclusive is False
    assert result.null_std >= 0.0


def test_static_model_runs():
    nm = NullModel(NullModelType.STATIC_NO_LEARNING_MODEL)
    result = nm.evaluate([0.3, 0.3, 0.3])
    assert result.distinguishable_from_null is False  # no change at all


def test_small_sample_returns_inconclusive():
    nm = NullModel(NullModelType.SYMBOL_LABEL_SHUFFLE)
    assert nm.evaluate([1, 2, 3]).inconclusive is True


def test_all_types_exist():
    for t in ("random_metric_shuffle", "time_index_shuffle",
              "event_order_shuffle", "symbol_label_shuffle",
              "world_edge_shuffle", "action_outcome_shuffle",
              "static_no_learning_model"):
        assert t in NullModelType.ALL


def test_unknown_type_rejected():
    with pytest.raises(ValueError):
        NullModel("bogus_null")


def test_cautious_language_in_notes():
    nm = NullModel(NullModelType.RANDOM_METRIC_SHUFFLE)
    result = nm.evaluate([float(i) for i in range(10)])
    joined = " ".join(result.notes).lower()
    assert "not a significance test" in joined or "cautious" in joined
