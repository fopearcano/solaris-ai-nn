"""SimulationBoundaryValidator: sim/counterfactual marked; debug blocked."""

from __future__ import annotations

from solaris_ai_nn.self_boundary import (
    BoundaryMarker,
    SimulationBoundaryValidator,
)


def test_simulation_marked():
    v = SimulationBoundaryValidator()
    m = v.mark("sim_1", BoundaryMarker.SIMULATION)
    assert m.marker == BoundaryMarker.SIMULATION
    assert m.is_observation is False


def test_counterfactual_marked():
    v = SimulationBoundaryValidator()
    m = v.mark("cf_1", BoundaryMarker.COUNTERFACTUAL)
    assert m.marker == BoundaryMarker.COUNTERFACTUAL
    assert m.is_observation is False


def test_debug_truth_blocked_from_perception():
    v = SimulationBoundaryValidator()
    assert v.validate_use_as_observation("dbg", BoundaryMarker.DEBUG_TRUTH) \
        is False
    assert v.validate_use_as_observation("sim", BoundaryMarker.SIMULATION) \
        is False
    assert v.warning_count() == 2


def test_real_observation_allowed():
    v = SimulationBoundaryValidator()
    assert v.validate_use_as_observation("obs", BoundaryMarker.OBSERVATION) \
        is True
    assert v.warning_count() == 0


def test_integrity_full_when_no_leak():
    v = SimulationBoundaryValidator()
    v.mark("s1", BoundaryMarker.SIMULATION)
    v.mark("o1", BoundaryMarker.OBSERVATION)
    # No non-observation marker was used as observation -> integrity 1.0.
    assert v.integrity() == 1.0
