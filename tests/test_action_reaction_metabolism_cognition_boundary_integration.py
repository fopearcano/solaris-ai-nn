"""Action-reaction updates metabolism/prediction/boundary via reactions."""

from __future__ import annotations

from solaris_ai_nn.action_reaction import (
    ActionCandidateRecord,
    ActionKind,
    ActionReactionRuntime,
    ReactionKind,
)
from solaris_ai_nn.desire_formation import DesireFormationRuntime


def _desire(tmp_path):
    des = DesireFormationRuntime(
        state_dir=str(tmp_path / "des"),
        metabolism={"novelty_appetite_pressure": 0.7}, max_ticks=1)
    des.update(tick=0)
    return des


def test_updates_metabolism_signals(tmp_path):
    ar = ActionReactionRuntime(state_dir=str(tmp_path / "ar"),
                               desire=_desire(tmp_path), max_ticks=1)
    # A no-op action reduces overload (metabolism-facing signal).
    ar.update(tick=0, extra_actions=[ActionCandidateRecord(kind=ActionKind.NO_OP)])
    signals = ar.metabolism_signals()
    assert "overload_reduced" in signals
    assert "constructive_reaction_count" in signals


def test_updates_prediction_outcome(tmp_path):
    ar = ActionReactionRuntime(state_dir=str(tmp_path / "ar"),
                               desire=_desire(tmp_path), max_ticks=1)
    ar.update(tick=0, extra_actions=[
        ActionCandidateRecord(kind=ActionKind.TEST_INTERNAL_PREDICTION)])
    kinds = {r.kind for r in ar.reactions}
    # A prediction test yields a prediction-outcome reaction.
    assert ReactionKind.PREDICTION_CONFIRMED in kinds or \
        ReactionKind.UNCERTAINTY_REDUCED in kinds


def test_updates_boundary_clarity(tmp_path):
    ar = ActionReactionRuntime(
        state_dir=str(tmp_path / "ar"), desire=_desire(tmp_path),
        self_boundary={"source_attribution_uncertainty_score": 0.6},
        max_ticks=1)
    ar.update(tick=0, extra_actions=[
        ActionCandidateRecord(kind=ActionKind.COMPARE_MODALITIES)])
    kinds = {r.kind for r in ar.reactions}
    assert ReactionKind.BOUNDARY_CLARIFIED in kinds or \
        ReactionKind.UNCERTAINTY_REDUCED in kinds
