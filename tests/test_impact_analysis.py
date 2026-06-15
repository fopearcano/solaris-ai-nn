"""ImpactAnalyzer: affected modules; safety explicit; unknown not low."""

from __future__ import annotations

from solaris_ai_nn.architecture_evolution import ImpactAnalyzer, ImpactSeverity


def test_affected_modules_detected():
    ia = ImpactAnalyzer().analyze("prune latent", ["latent"],
                                  integration_count=4)
    assert "latent" in ia.affected_modules
    assert ia.affected_tests and ia.affected_examples


def test_safety_impact_explicit():
    ia = ImpactAnalyzer().analyze("prune ego", ["ego"],
                                  safety_critical_touched=True)
    assert ia.safety_impact == ImpactSeverity.HIGH
    assert ia.has_safety_impact is True
    assert ia.affected_areas["safety_invariants"] == ImpactSeverity.HIGH


def test_unknown_impact_not_low():
    # A change with no integration touches -> areas default to UNKNOWN, not LOW.
    ia = ImpactAnalyzer().analyze("prune isolated", ["isolated"],
                                  integration_count=0)
    assert ia.affected_areas["governance"] == ImpactSeverity.UNKNOWN
    assert ia.state_compatibility_risk == ImpactSeverity.UNKNOWN


def test_state_touch_is_high_risk():
    ia = ImpactAnalyzer().analyze("change state schema", ["memory"],
                                  touches_state=True)
    assert ia.state_compatibility_risk == ImpactSeverity.HIGH


def test_does_not_implement_change():
    ia = ImpactAnalyzer().analyze("prune latent", ["latent"])
    joined = " ".join(ia.limitations).lower()
    assert "implements nothing" in joined
    assert "never as low" in joined
