"""Tests for the homeostatic variables."""

from __future__ import annotations

from solaris_ai_nn.homeostasis.variables import (
    VARIABLE_GROUPS,
    HomeostaticState,
    VariableRange,
    VariableTrend,
    clamp01,
    normalize,
)


def test_normalization_utilities():
    assert normalize(5.0, 0.0, 10.0) == 0.5
    assert normalize(-3.0, 0.0, 10.0) == 0.0
    assert normalize(15.0, 0.0, 10.0) == 1.0
    assert clamp01(1.7) == 1.0 and clamp01(-0.2) == 0.0


def test_variables_normalize_and_keep_raw():
    state = HomeostaticState()
    variable = state.upsert("body_energy", normalize(2.5, 0.0, 10.0),
                            source="embodiment", raw=2.5)
    assert variable.value == 0.25
    assert variable.metadata["raw_value"] == 2.5  # raw never hidden
    assert "embodiment" in variable.source_modules


def test_deviation_computed():
    # body_energy targets 1.0; low energy deviates strongly.
    state = HomeostaticState()
    low = state.upsert("body_energy", 0.2)
    assert low.deviation == 0.8
    # novelty_pressure targets a range; inside it deviation is zero.
    in_range = state.upsert("novelty_pressure", 0.3)
    assert in_range.deviation == 0.0
    out_of_range = state.upsert("novelty_pressure", 0.9)
    assert out_of_range.deviation > 0.0
    point = VariableRange(target=0.0)
    assert point.deviation(0.4) == 0.4


def test_urgency_computed_with_weights():
    state = HomeostaticState()
    danger = state.upsert("danger_proximity", 0.8)   # weight 1.4
    low_stim = state.upsert("low_stimulus_pressure", 0.8)  # weight 0.6
    assert danger.urgency > low_stim.urgency
    assert state.most_urgent(1)[0].name == "danger_proximity"


def test_trends_update():
    state = HomeostaticState()
    for value in (0.2, 0.2, 0.2):
        state.upsert("fatigue", value)
    assert state.get("fatigue").trend == VariableTrend.STABLE
    for value in (0.4, 0.6, 0.8):
        state.upsert("fatigue", value)
    assert state.get("fatigue").trend == VariableTrend.RISING
    for value in (0.6, 0.4, 0.2):
        state.upsert("fatigue", value)
    assert state.get("fatigue").trend == VariableTrend.FALLING
    fresh = state.upsert("trace_pressure", 0.5)
    assert fresh.trend == VariableTrend.UNKNOWN


def test_all_spec_groups_defined():
    assert set(VARIABLE_GROUPS) == {"continuity", "energy", "safety",
                                    "novelty", "memory", "social",
                                    "embodiment"}
    state = HomeostaticState()
    state.upsert("danger_proximity", 0.5)
    assert state.group("embodiment")[0].name == "danger_proximity"
    data = state.to_dict()
    assert "variables" in data and "most_urgent" in data
