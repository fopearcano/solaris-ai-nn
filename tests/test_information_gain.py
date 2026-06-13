"""Tests for the information-gain estimator."""

from __future__ import annotations

from solaris_ai_nn.active_perception.information_gain import (
    InformationGainEstimator,
)
from solaris_ai_nn.active_perception.sampling_actions import (
    SamplingAction,
    SamplingActionType,
    SamplingScope,
)


def _action(atype, scope=SamplingScope.SIMULATION_ONLY, target=None):
    return SamplingAction(action_type=atype, scope=scope, target_ref=target)


def test_estimates_action_value_with_confidence():
    est = InformationGainEstimator()
    ctx = {"world_model": {"graph_node_count": 10, "unknown_node_count": 5,
                           "prediction_accuracy": 0.4},
           "mysterium_pressure": 0.5, "proto_language": {}, "ecology": {}}
    e = est.estimate_action(
        _action(SamplingActionType.SAMPLE_UNKNOWN_REGION,
                target="unknown_region"), ctx)
    assert 0.0 <= e.expected_gain <= 1.0
    assert 0.0 <= e.confidence <= 1.0
    assert 0.0 <= e.uncertainty <= 1.0


def test_weak_evidence_caps_gain():
    est = InformationGainEstimator()
    e = est.estimate_action(
        _action(SamplingActionType.SAMPLE_UNKNOWN_REGION), {})
    assert e.expected_gain <= 0.1
    assert "weak evidence" in e.basis


def test_compare_actions_sorted():
    est = InformationGainEstimator()
    ctx = {"world_model": {"graph_node_count": 10, "unknown_node_count": 6,
                           "prediction_accuracy": 0.3}}
    inspect = _action(SamplingActionType.SAMPLE_UNKNOWN_REGION,
                      target="unknown_region")
    wait = _action(SamplingActionType.WAIT, SamplingScope.INTERNAL_ONLY)
    ranked = est.compare_actions([wait, inspect], ctx)
    assert ranked[0].action_type == "sample_unknown_region"


def test_observed_result_score():
    est = InformationGainEstimator()
    action = _action(SamplingActionType.REPLAY_UNCERTAIN_TRACE,
                     SamplingScope.INTERNAL_ONLY)
    before = {"mysterium_pressure": 0.8,
              "world_model": {"prediction_accuracy": 0.4}}
    after = {"mysterium_pressure": 0.5,
             "world_model": {"prediction_accuracy": 0.6}}
    observed = est.score_observed_result(action, None, before, after)
    assert observed > 0
    assert est.snapshot()["scored_actions"] == 1
