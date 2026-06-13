"""Integration: auto-regeneration and the hypothesis engine."""

from __future__ import annotations

from solaris_ai_nn.autoregeneration.graph_hygiene import (
    WorldModelHygieneManager,
)


def test_contradiction_repair_requests_hypothesis_test():
    mgr = WorldModelHygieneManager()
    mgr.propose({"world_model": {
        "contradiction_edges": ["a|contradicts|b"]}})
    # The unresolved contradiction is queued for a hypothesis test.
    assert mgr.hypothesis_requests == ["a|contradicts|b"]


def test_offline_evidence_not_enough_for_irreversible_repair():
    from solaris_ai_nn.autoregeneration import (
        AutoRegenerationSafetyValidator,
        make_repair,
        RepairActionType,
    )

    v = AutoRegenerationSafetyValidator()
    action = make_repair(RepairActionType.WEAKEN_CONTRADICTORY_EDGE,
                         target_ref="a|contradicts|b")
    action.reversible = False
    # Offline/counterfactual evidence cannot justify an irreversible repair.
    assert not v.validate_repair_action(
        action, {"evidence_offline_only": True}).safe


def test_reversible_repair_allowed_with_offline_evidence():
    from solaris_ai_nn.autoregeneration import (
        AutoRegenerationSafetyValidator,
        make_repair,
        RepairActionType,
    )

    v = AutoRegenerationSafetyValidator()
    action = make_repair(RepairActionType.MARK_WORLD_EDGE_AMBIGUOUS,
                         target_ref="a|contradicts|b")  # reversible
    assert v.validate_repair_action(
        action, {"evidence_offline_only": True}).safe
