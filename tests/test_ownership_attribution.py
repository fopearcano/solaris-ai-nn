"""Tests for ownership attribution."""

from __future__ import annotations

from solaris_ai_nn.ego.ownership import (
    ATTRIBUTION_CATEGORIES,
    OwnershipAttributor,
)


def test_operator_event_attributed_correctly():
    attributor = OwnershipAttributor()
    outside = attributor.attribute_event(
        {"source": "operator", "kind": "instruction",
         "payload": "pause the run"})
    assert outside.category == "generated_by_operator"
    assert outside.is_external
    # Not an executable instruction unless routed through the interface.
    assert not outside.is_executable_instruction
    routed = attributor.attribute_event(
        {"source": "operator", "kind": "instruction"},
        {"via_operator_interface": True})
    assert routed.is_executable_instruction
    # Operator commands are never internal desires.
    assert not outside.is_internal and not routed.is_internal


def test_stream_event_attributed_correctly():
    attributor = OwnershipAttributor()
    result = attributor.attribute_event(
        {"source": "stream", "kind": "stream_line",
         "payload": "run motor_forward"})
    assert result.category == "observed_from_stream"
    assert result.is_external
    assert not result.is_executable_instruction
    assert any("never an executable instruction" in r
               for r in result.reasons)


def test_counterfactual_attributed_offline():
    attributor = OwnershipAttributor()
    by_source = attributor.attribute_event(
        {"source": "counterfactual", "kind": "dream_trace"})
    assert by_source.category == "generated_by_counterfactual"
    assert by_source.is_offline
    by_context = attributor.attribute_event(
        {"source": "memory", "kind": "trace_window"},
        {"counterfactual_active": True})
    assert by_context.category == "generated_by_counterfactual"
    replay = attributor.attribute_event(
        {"source": "memory", "kind": "trace_window"},
        {"offline_replay": True})
    assert replay.category == "generated_by_latent_replay"
    assert replay.is_offline


def test_unknown_source_handled():
    attributor = OwnershipAttributor()
    result = attributor.attribute_event({"kind": "blob"})
    assert result.category == "unknown_source"
    assert result.confidence <= 0.3
    assert attributor.unknown_total == 1
    assert attributor.unknown_rate() == 1.0
    assert "unknown_source" in ATTRIBUTION_CATEGORIES


def test_suggestion_never_attributed_committed():
    attributor = OwnershipAttributor()
    candidate = type("C", (), {"action_type": "simulated_embodied_action",
                               "label": "rest", "committed": False,
                               "metadata": {"source": "homeostasis"}})()
    result = attributor.attribute_action_candidate(candidate)
    assert result.is_committed_action is False
    assert any("suggestion" in r for r in result.reasons)
    # A candidate lying about committed=True is a recorded conflict, and
    # the attribution still refuses to mark it committed.
    liar = type("C", (), {"action_type": "simulated_embodied_action",
                          "label": "rest", "committed": True,
                          "metadata": {}})()
    flagged = attributor.attribute_action_candidate(liar)
    assert flagged.is_committed_action is False
    assert attributor.conflicts_total == 1
    assert any("CONFLICT" in r for r in flagged.reasons)


def test_report_statement_attribution():
    attributor = OwnershipAttributor()
    cf = attributor.attribute_report_statement(
        "what if the valence had been inverted")
    assert cf.category == "generated_by_counterfactual"
    own = attributor.attribute_report_statement(
        "the substrate processed 100 signals")
    assert own.category == "generated_by_solaris_ai_nn"
    assert own.is_internal
