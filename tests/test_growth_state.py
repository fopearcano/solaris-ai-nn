"""DevelopmentalGrowthState: dimensions computed; pruning counts; no IQ score."""

from __future__ import annotations

from solaris_ai_nn.developmental_life import (
    DevelopmentalGrowthState,
    GrowthDimension,
)


def _statuses():
    return {
        "perceptual_metabolism": {"source_diet_diversity": 0.5,
                                  "consolidation_pressure_score": 0.4},
        "perceptual_ontogenesis": {"proto_concept_count": 10,
                                   "stable_concept_count": 5,
                                   "decaying_concept_count": 2,
                                   "human_label_contamination_score": 0.1},
        "semiogenesis": {"internal_sign_count": 8, "stable_sign_count": 4,
                         "private_syntax_pattern_count": 6,
                         "contaminated_sign_ratio": 0.1},
        "sensorium_cognition": {"prediction_success_rate": 0.6},
        "self_boundary": {"boundary_confidence_score": 0.7,
                          "continuity_break_count": 0,
                          "body_schema_stability": 0.8},
        "action_reaction": {"learned_effect_count": 3,
                            "strengthened_habit_count": 1}}


def test_growth_dimensions_computed():
    gs = DevelopmentalGrowthState()
    gs.update(_statuses())
    assert len(gs.dimensions) == len(GrowthDimension.ALL)
    assert 0.0 <= gs.composite() <= 1.0
    assert gs.dimensions[GrowthDimension.PREDICTION_SKILL] == 0.6


def test_pruning_and_decay_can_count_as_growth():
    gs = DevelopmentalGrowthState()
    gs.update(_statuses())
    # Decay management is a tracked growth dimension (pruning/decay counts).
    assert GrowthDimension.CONCEPT_DECAY_MANAGEMENT in gs.dimensions
    assert gs.dimensions[GrowthDimension.CONCEPT_DECAY_MANAGEMENT] > 0.0


def test_no_intelligence_score():
    gs = DevelopmentalGrowthState()
    gs.update(_statuses())
    note = gs.to_dict()["note"].lower()
    assert "not an intelligence score" in note
    assert "more is not\n                    always better" in note or \
        "more is not" in note


def test_signals_track_change():
    gs = DevelopmentalGrowthState()
    gs.update(_statuses())
    prior = dict(gs.dimensions)
    boosted = _statuses()
    boosted["sensorium_cognition"]["prediction_success_rate"] = 0.9
    gs.update(boosted, prior=prior)
    pred_signal = [s for s in gs.signals
                   if s.dimension == GrowthDimension.PREDICTION_SKILL][0]
    assert pred_signal.direction == "increase"
