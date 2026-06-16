"""Limitation registry: warning/major/critical; critical blocks; visible."""

from __future__ import annotations

from solaris_ai_nn.research_baseline import (
    BaselineLimitationRegistry,
    LimitationCategory,
    LimitationSeverity,
    build_limitation_registry,
)


def test_warning_major_critical_limitations():
    reg = BaselineLimitationRegistry()
    reg.add(LimitationCategory.INSUFFICIENT_REPLICATION,
            LimitationSeverity.WARNING)
    reg.add(LimitationCategory.MISSING_LIVE_DATA, LimitationSeverity.MAJOR)
    reg.add(LimitationCategory.WEAK_SAFETY_EVIDENCE, LimitationSeverity.CRITICAL)
    d = reg.to_dict()
    assert d["limitation_count"] == 3
    assert d["critical_limitation_count"] == 1
    assert d["major_limitation_count"] == 1


def test_critical_blocks_validation():
    reg = BaselineLimitationRegistry()
    reg.add(LimitationCategory.WEAK_SAFETY_EVIDENCE, LimitationSeverity.CRITICAL)
    assert reg.blocks_validation is True


def test_warnings_only_does_not_block():
    reg = BaselineLimitationRegistry()
    reg.add(LimitationCategory.MISSING_LIVE_DATA, LimitationSeverity.MAJOR)
    assert reg.blocks_validation is False
    assert reg.warnings_only is True


def test_limitations_visible():
    reg = BaselineLimitationRegistry()
    reg.add(LimitationCategory.FIXTURE_OVERFIT_RISK, LimitationSeverity.WARNING,
            detail="fixture-weighted evidence")
    d = reg.to_dict()
    assert d["limitations"][0]["category"] == \
        LimitationCategory.FIXTURE_OVERFIT_RISK
    assert d["limitations"][0]["detail"] == "fixture-weighted evidence"


def test_builder_derives_from_evidence():
    reg = build_limitation_registry(
        post_merge={"critical_regression_count": 1},
        intake={"critical_safety_regression_count": 1, "coverage_gap_count": 2},
        snapshot={"missing": ["replication_report", "soak_dossier"]},
        validation={"validation_missing_count": 1})
    d = reg.to_dict()
    assert d["critical_limitation_count"] >= 1
    assert d["blocks_validation"] is True
