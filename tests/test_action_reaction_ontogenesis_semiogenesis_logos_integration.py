"""Action-reaction updates concept/sign utility and emits LOGOS tensions."""

from __future__ import annotations

from solaris_ai_nn.action_reaction import (
    ActionCandidateRecord,
    ActionKind,
    ActionReactionRuntime,
)
from solaris_ai_nn.desire_formation import DesireFormationRuntime


def _runtime(tmp_path, extra=None, no_effect=False):
    des = DesireFormationRuntime(
        state_dir=str(tmp_path / "des"),
        metabolism={"novelty_appetite_pressure": 0.7},
        cognition={"failed_prediction_count": 2}, max_ticks=1)
    des.update(tick=0)
    ar = ActionReactionRuntime(state_dir=str(tmp_path / "ar"), desire=des,
                               max_ticks=2)
    for t in range(2):
        ar.update(tick=t, extra_actions=extra if t == 0 else None,
                  no_effect=no_effect)
    return ar


def test_concept_sign_utility_updated(tmp_path):
    # Marking a concept unstable / a sign ambiguous produces concept/sign-change
    # consequences that ontogenesis/semiogenesis can consume.
    ar = _runtime(tmp_path, extra=[
        ActionCandidateRecord(kind=ActionKind.MARK_CONCEPT_UNSTABLE),
        ActionCandidateRecord(kind=ActionKind.TRIGGER_CONSOLIDATION)])
    ctypes = {c.consequence_type for c in ar.consequences}
    assert "concept_change" in ctypes or "sign_change" in ctypes


def test_logos_tension_emitted(tmp_path):
    ar = _runtime(tmp_path, extra=[ActionCandidateRecord(kind="actuate_robot")])
    tensions = ar.logos_tensions()
    from solaris_ai_nn.logos_complexity.tension import TensionType
    assert tensions
    assert all(t.tension_type in TensionType.ALL for t in tensions)
    assert any("action_reaction_tension" in t.metadata for t in tensions)


def test_no_effect_emits_no_action_tension(tmp_path):
    ar = _runtime(tmp_path, no_effect=True)
    tensions = ar.logos_tensions()
    assert any(t.metadata.get("action_reaction_tension") == "no_action_vs_pressure"
               for t in tensions)
