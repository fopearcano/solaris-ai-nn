"""Tests for the developmental safety validator."""

from __future__ import annotations

from solaris_ai_nn.developmental.memory_layers import MemoryLayerManager
from solaris_ai_nn.developmental.safety import (
    HARD_RULES,
    DevelopmentalSafetyValidator,
)


class _Runtime:
    enable_month_scale = False
    enable_year_scale = False
    max_steps = 100
    max_duration_s = None


def test_unbounded_month_mode_blocked():
    validator = DevelopmentalSafetyValidator()
    runtime = _Runtime()
    runtime.enable_month_scale = True
    report = validator.validate_config(runtime, governance=None)
    assert not report.safe
    assert "month-scale" in report.violations[0]
    unbounded = _Runtime()
    unbounded.max_steps = None
    report2 = validator.validate_config(unbounded, governance=None)
    assert not report2.safe
    assert "bounded" in report2.violations[0]


def test_memory_overgrowth_warned():
    validator = DevelopmentalSafetyValidator()
    manager = MemoryLayerManager(budgets={"hot": 5, "warm": 2,
                                          "cold": 2, "fossil": 2})
    # Force an over-budget warm layer directly (bypassing auto-compress).
    from solaris_ai_nn.developmental.memory_layers import MemoryItem

    manager.layers["warm"] = [MemoryItem(layer="warm",
                                         evidence_summary="x")
                              for _ in range(5)]
    report = validator.validate_memory(manager)
    assert not report.safe
    assert "over budget" in report.violations[0]


def test_pruning_without_summary_blocked():
    validator = DevelopmentalSafetyValidator()
    report = validator.validate_pruning(["item"], summary="")
    assert not report.safe
    assert "silently destroyed" in report.violations[0]
    assert validator.validate_pruning(["item"],
                                      summary="3 events summarized").safe


def test_counterfactual_cannot_become_real_history():
    validator = DevelopmentalSafetyValidator()

    class FakeEvent:
        text = ("the counterfactual replay actually happened in the "
                "world")
        simulated = True

    report = validator.validate_history_event(FakeEvent())
    assert not report.safe
    assert "real observation" in report.violations[0]


def test_unsafe_report_claim_blocked():
    validator = DevelopmentalSafetyValidator()
    report = validator.validate_report(
        "After three months the system is alive and is conscious.")
    assert not report.safe
    assert any("self-description" in v for v in report.violations)
    safe = validator.validate_report(
        "After three simulated months the structural change score was "
        "0.3 with 8 fossil records.")
    assert safe.safe


def test_paths_validated_and_hard_rules():
    validator = DevelopmentalSafetyValidator()
    assert not validator.validate_paths("/etc/solaris").safe
    assert validator.validate_paths(".solaris_ai_nn_state/dev").safe
    assert len(HARD_RULES) == 9
