"""Tests for symbol combinatorics."""

from __future__ import annotations

import json

from solaris_ai_nn.protolanguage.combinatorics import SymbolCombinator

STREAM = ["ABS_0001", "NEED_SIGNAL_0001", "ACT_LOOK_0001"]


def test_repeated_sequence_detected():
    combinator = SymbolCombinator()
    for i in range(5):
        combinator.observe_sequence(STREAM, {"label": f"w{i}"})
    repeated = combinator.find_repeated_sequences(min_count=3)
    assert repeated
    keys = {s.key for s in repeated}
    assert "ABS_0001>NEED_SIGNAL_0001>ACT_LOOK_0001" in keys
    assert "ABS_0001>NEED_SIGNAL_0001" in keys  # bigrams too
    best = repeated[0]
    assert best.count == 5
    # One observation of something else does not register as repeated.
    combinator.observe_sequence(["X_0001", "Y_0001"])
    assert "X_0001>Y_0001" not in {
        s.key for s in combinator.find_repeated_sequences(3)}


def test_utility_score_computed():
    combinator = SymbolCombinator()
    for _ in range(6):
        combinator.observe_sequence(STREAM, {"outcome_valence": 0.5})
    sequence = combinator.find_repeated_sequences(3)[0]
    utility = combinator.score_sequence_utility(sequence)
    assert 0 < utility <= 1.0
    assert sequence.utility == utility
    # Deterministic transitions raise the score component.
    assert combinator.transition_counts["ABS_0001"][
        "NEED_SIGNAL_0001"] == 6


def test_sequence_snapshot_serializes():
    combinator = SymbolCombinator()
    for _ in range(4):
        combinator.observe_sequence(STREAM, {"label": "w",
                                             "outcome_valence": 0.2})
    snapshot = combinator.snapshot()
    json.dumps(snapshot, default=str)
    assert snapshot["repeated_sequence_count"] >= 1
    assert "not sentences" in snapshot["note"]
    sequence_dict = snapshot["top_sequences"][0]
    assert sequence_dict["mean_valence"] == 0.2
    assert "not a sentence" in sequence_dict["note"]
