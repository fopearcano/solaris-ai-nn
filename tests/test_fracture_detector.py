"""Tests for the LOGOS fracture detector."""

from __future__ import annotations

from solaris_ai_nn.logos_complexity.fracture import FractureDetector
from solaris_ai_nn.logos_complexity.tension import TensionType


def test_detects_world_model_contradiction():
    det = FractureDetector()
    tensions = det.scan({"world_model": {
        "contradiction_edges": ["a|contradicts|b"]}})
    assert any(t.tension_type == TensionType.WORLD_MODEL_CONTRADICTION
               for t in tensions)


def test_detects_proto_symbol_ambiguity():
    det = FractureDetector()
    tensions = det.scan({"proto_language": {
        "symbol_count": 10, "ambiguous_symbol_count": 5,
        "ambiguous_symbols": ["S1"]}})
    assert any(t.tension_type == TensionType.SYMBOL_AMBIGUITY
               for t in tensions)


def test_detects_prediction_failure():
    det = FractureDetector()
    tensions = det.scan({"world_model": {"prediction_accuracy": 0.2}})
    assert any(t.tension_type == TensionType.PREDICTION_FAILURE
               for t in tensions)


def test_no_mutation_during_scan():
    import copy

    det = FractureDetector()
    ctx = {"world_model": {"contradiction_edges": ["a|c|b"]},
           "proto_language": {"symbol_count": 10,
                              "ambiguous_symbol_count": 5}}
    before = copy.deepcopy(ctx)
    det.scan(ctx)
    assert ctx == before


def test_partial_and_corrupt_context_safe():
    det = FractureDetector()
    state = det.scan({"world_model": "not a dict", "proto_language": None})
    assert isinstance(state, list)


def test_empty_context_no_tensions():
    det = FractureDetector()
    assert det.scan({}) == []


def test_snapshot_shape():
    det = FractureDetector()
    det.scan({"mysterium_pressure": 0.6})
    snap = det.snapshot()
    assert snap["scans_run"] == 1
    assert "by_type" in snap
