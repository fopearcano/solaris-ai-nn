"""Falsification lab: shuffled order, random labels, passive parser, no mutation."""

from __future__ import annotations

from solaris_ai_nn.developmental_replication import (
    FalsificationOutcome,
    FalsificationTest,
    FalsificationTestType,
)


def test_shuffled_order_test_works():
    lab = FalsificationTest()
    # Prediction collapses under shuffle -> the claim survives (passed).
    passed = lab.run(FalsificationTestType.SHUFFLED_EVENT_ORDER,
                     run_profile={"durable_prediction_improvement_score": 0.8},
                     null_profile={"durable_prediction_improvement_score": 0.1})
    assert passed.outcome == FalsificationOutcome.PASSED
    # Prediction survives shuffle -> the claim is falsified.
    falsified = lab.run(
        FalsificationTestType.SHUFFLED_EVENT_ORDER,
        run_profile={"durable_prediction_improvement_score": 0.8},
        null_profile={"durable_prediction_improvement_score": 0.78})
    assert falsified.outcome == FalsificationOutcome.FALSIFIED


def test_random_label_test_works():
    lab = FalsificationTest()
    result = lab.run(
        FalsificationTestType.RANDOM_LABELS_SAME_FEATURES,
        run_profile={"concept_family_distribution": {"rf": 3, "vib": 2}},
        null_profile={"concept_family_distribution": {"rf": 3, "vib": 2}})
    assert result.outcome == FalsificationOutcome.PASSED


def test_passive_parser_comparison_works():
    lab = FalsificationTest()
    result = lab.run(
        FalsificationTestType.PASSIVE_PARSER_COMPARISON,
        run_profile={"sign_family_distribution": {"s1": 2, "s2": 1}},
        null_profile={"sign_family_distribution": {"s1": 2, "s2": 1}})
    # Passive parser reproduces the same families -> the stack added nothing.
    assert result.outcome == FalsificationOutcome.FALSIFIED


def test_profile_only_tests_run_without_null():
    lab = FalsificationTest()
    result = lab.run(FalsificationTestType.LOG_ACCUMULATION_NULL,
                     run_profile={"structural_growth_status":
                                  "mere_event_accumulation"})
    assert result.outcome == FalsificationOutcome.FALSIFIED


def test_original_artifacts_not_modified():
    lab = FalsificationTest()
    original = {"durable_prediction_improvement_score": 0.8,
                "concept_family_distribution": {"rf": 3}}
    snapshot = dict(original)
    result = lab.run(FalsificationTestType.SHUFFLED_EVENT_ORDER,
                     run_profile=original,
                     null_profile={"durable_prediction_improvement_score": 0.1})
    assert original == snapshot  # untouched
    assert result.original_modified is False


def test_passing_does_not_prove_understanding():
    lab = FalsificationTest()
    result = lab.run(FalsificationTestType.FIXTURE_OVERFIT_PROBE,
                     run_profile={"structural_growth_status":
                                  "real_structural_growth"})
    assert "does not prove" in result.to_dict()["note"]
