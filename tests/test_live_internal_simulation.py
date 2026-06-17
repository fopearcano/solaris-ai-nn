"""Live internal simulation: generated, max steps respected, controls nothing."""

from __future__ import annotations

from solaris_ai_nn.live_cognition import (
    AnticipationCandidate,
    LiveInternalSimulation,
)


def _ants():
    return [
        AnticipationCandidate(anticipation_id="a1",
                              anticipation_type="rhythm_continuation",
                              sign_id="s1", uncertainty=0.4),
        AnticipationCandidate(anticipation_id="a2",
                              anticipation_type="recurrence_expected",
                              sign_id="s2", uncertainty=0.5),
        AnticipationCandidate(anticipation_id="a3",
                              anticipation_type="co_occurrence_expected",
                              sign_id="s3", uncertainty=0.5),
    ]


def test_simulation_generated():
    sims = LiveInternalSimulation(max_steps=6).simulate(_ants())
    assert len(sims) == 3


def test_max_steps_respected():
    sims = LiveInternalSimulation(max_steps=3).simulate(_ants())
    assert all(s.step_count <= 3 for s in sims)


def test_no_action_or_control():
    sims = LiveInternalSimulation().simulate(_ants())
    for s in sims:
        d = s.to_dict()
        assert d["controls_feeders"] is False
        assert d["executes_commands"] is False
        assert d["acts_in_world"] is False
        assert d["is_offline_metadata"] is True


def test_uncertainty_preserved():
    sims = LiveInternalSimulation().simulate(_ants())
    assert all(s.uncertainty > 0 for s in sims)
    assert all(s.status == "not_yet_observed" for s in sims)


def test_contaminated_anticipation_skipped():
    ant = AnticipationCandidate(anticipation_id="bad",
                                anticipation_type="recurrence_expected",
                                sign_id="s", uncertainty=1.0,
                                status="contaminated")
    sims = LiveInternalSimulation().simulate([ant])
    assert sims == []
