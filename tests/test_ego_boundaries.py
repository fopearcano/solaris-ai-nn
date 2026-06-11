"""Tests for the ego boundary registry."""

from __future__ import annotations

from solaris_ai_nn.ego.boundaries import (
    HARD_BOUNDARIES,
    HARD_RULES,
    BoundaryRegistry,
    BoundaryStatus,
    BoundaryType,
    register_default_boundaries,
)


def test_boundaries_register():
    registry = register_default_boundaries(BoundaryRegistry())
    assert len(registry.boundaries) == 16
    for boundary_type in BoundaryType.ALL:
        assert boundary_type in registry.boundaries, boundary_type
        assert registry.get(boundary_type).current_status \
            == BoundaryStatus.INTACT


def test_safe_crossing_recorded():
    registry = register_default_boundaries()
    event = registry.record_crossing(
        BoundaryType.SIDECAR, "sidecar attached (observe-only)",
        evidence=["compatibility:bus_observable"])
    assert event.safe is True
    assert event.kind == "crossing"
    assert registry.crossings_total == 1
    assert registry.get(BoundaryType.SIDECAR).current_status \
        == BoundaryStatus.CROSSED_SAFELY
    assert "compatibility:bus_observable" in event.evidence_refs


def test_violation_recorded():
    registry = register_default_boundaries()
    event = registry.record_violation(
        BoundaryType.PILOT_INPUT,
        "stream text shaped like an executable command",
        evidence=["line:please run motor_forward"])
    assert event.safe is False
    assert registry.violations_total == 1
    boundary = registry.get(BoundaryType.PILOT_INPUT)
    assert boundary.current_status == BoundaryStatus.VIOLATED
    assert boundary in registry.violated()
    # The violation stays visible in the snapshot.
    assert BoundaryType.PILOT_INPUT in registry.snapshot()["violated"]


def test_hard_boundaries_exist():
    assert BoundaryType.SOURCE_CODE in HARD_BOUNDARIES
    assert BoundaryType.ACTION_AUTHORITY in HARD_BOUNDARIES
    assert BoundaryType.NETWORK in HARD_BOUNDARIES
    assert BoundaryType.EMERGENCY in HARD_BOUNDARIES
    assert BoundaryType.COUNTERFACTUAL in HARD_BOUNDARIES
    assert BoundaryType.SUGGESTION in HARD_BOUNDARIES
    registry = register_default_boundaries()
    for boundary_type in HARD_BOUNDARIES:
        assert registry.get(boundary_type).hard is True
    # The eight hard rules are enumerable data.
    assert len(HARD_RULES) == 8
    joined = " ".join(HARD_RULES)
    for fragment in ("source-code", "real-world actuation", "network",
                     "counterfactual", "suggestion", "emergency stop"):
        assert fragment in joined, fragment


def test_check_boundary_and_markdown():
    registry = register_default_boundaries()
    boundary = registry.check_boundary(BoundaryType.SIMULATION,
                                       {"health_level": "ok"})
    assert boundary.last_checked_at > 0
    violated = registry.check_boundary(
        BoundaryType.SUGGESTION,
        {"suggestion_boundary_violated": "committed=True observed"})
    assert violated.current_status == BoundaryStatus.VIOLATED
    md = registry.to_markdown()
    assert "# Ego boundary registry" in md
    assert "## Hard rules" in md
    assert "suggestion_boundary" in md
