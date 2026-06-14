"""BoundaryRegressionSuite: sensory/motor/sim-real boundaries; crossing fails."""

from __future__ import annotations

from solaris_ai_nn.safety_invariants import (
    BoundaryRegressionSuite,
    BoundaryTestResult,
    BoundaryTestStatus,
)


def test_sensory_boundary_tested():
    r = BoundaryRegressionSuite().test_sensory_input_boundary()
    assert r.boundary == "sensory_input"
    assert r.passed is True
    assert r.boundary_crossed is False


def test_motor_boundary_tested():
    r = BoundaryRegressionSuite().test_motor_action_boundary()
    assert r.boundary == "motor_action"
    assert r.passed is True


def test_actuation_firewall_boundary_holds():
    r = BoundaryRegressionSuite().test_actuation_firewall_boundary()
    assert r.passed is True and r.boundary_crossed is False


def test_simulation_real_boundary_tested():
    r = BoundaryRegressionSuite().test_simulated_real_evidence_boundary()
    assert r.boundary == "simulated_real_evidence"
    assert r.passed is True


def test_all_boundaries_hold():
    summary = BoundaryRegressionSuite().summary()
    assert summary["all_held"] is True
    assert summary["boundaries_crossed"] == []
    assert summary["boundary_count"] == 11


def test_boundary_crossing_fails():
    # A crossed boundary is a fail with boundary_crossed True.
    r = BoundaryTestResult(boundary="x", status=BoundaryTestStatus.FAIL,
                           boundary_crossed=True)
    assert r.passed is False
