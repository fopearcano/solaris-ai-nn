"""Tests for symbol prediction utility."""

from __future__ import annotations

import random

from solaris_ai_nn.protolanguage.prediction_utility import (
    SymbolPredictionEvaluator,
)

LOOP = ["ABS_0001", "NEED_0001", "ACT_0001", "RCT_0001"]


def test_markov_style_prediction_works():
    evaluator = SymbolPredictionEvaluator()
    evaluator.train_counts([LOOP] * 5)
    prediction, probability = evaluator.predict_next(["ABS_0001"])
    assert prediction == "NEED_0001"
    assert probability == 1.0
    # Longer context wins when available.
    prediction2, _ = evaluator.predict_next(["ABS_0001", "NEED_0001"])
    assert prediction2 == "ACT_0001"


def test_baseline_comparison_works():
    evaluator = SymbolPredictionEvaluator()
    evaluator.train_counts([LOOP] * 6)
    comparison = evaluator.evaluate_holdout([LOOP] * 2)
    assert comparison["predictions_scored"] == 6
    assert comparison["symbolic_accuracy"] == 1.0
    assert comparison["baseline_accuracy"] < 1.0  # frequency guess
    assert comparison["improvement_over_baseline"] > 0
    assert comparison["improved"] is True


def test_no_improvement_reported_honestly():
    rng = random.Random(3)
    vocabulary = [f"SIG_{c}_0001" for c in "ABCDE"]
    noise = [[rng.choice(vocabulary) for _ in range(4)]
             for _ in range(12)]
    evaluator = SymbolPredictionEvaluator()
    evaluator.train_counts(noise[:8])
    comparison = evaluator.evaluate_holdout(noise[8:])
    assert "improvement_over_baseline" in comparison
    assert comparison["improvement_over_baseline"] is not None
    # Honest wording either way.
    assert "honestly" in comparison["note"]
    assert isinstance(comparison["improved"], bool)


def test_scores_feed_back_into_registry():
    from solaris_ai_nn.protolanguage.symbol_registry import (
        SymbolRegistry,
    )
    from solaris_ai_nn.protolanguage.symbols import SymbolType

    registry = SymbolRegistry()
    symbol = registry.upsert_symbol(SymbolType.ABSENCE, "silence",
                                    evidence_refs=["a:1"])
    evaluator = SymbolPredictionEvaluator()
    evaluator.train_counts([[symbol.token, "NEED_0001"]] * 4)
    evaluator.evaluate_holdout([[symbol.token, "NEED_0001"]])
    evaluator.update_symbol_scores(registry)
    assert symbol.prediction_score > 0
