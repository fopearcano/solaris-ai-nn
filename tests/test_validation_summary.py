"""Validation summary: statuses computed, safety failure + missing block."""

from __future__ import annotations

from solaris_ai_nn.research_baseline import (
    BaselineValidationSummary,
    ValidationStatus,
)


def test_validation_statuses_computed():
    vs = BaselineValidationSummary().build(validation_results={
        "unit_tests": {"passed": True}, "safety_tests": {"passed": True},
        "claimguard": {"safe": True}, "safety_invariants": {"passed": True},
        "documentation": {"passed": True}})
    d = vs.to_dict()
    assert d["statuses"]["unit_tests"] == ValidationStatus.PASSED
    assert d["validation_pass_count"] >= 4
    assert d["blocks_validation"] is False


def test_safety_failure_blocks():
    vs = BaselineValidationSummary().build(validation_results={
        "unit_tests": {"passed": True}, "safety_tests": {"failed": True},
        "claimguard": {"safe": True}, "safety_invariants": {"passed": True}})
    assert vs.safety_failed is True
    assert vs.blocks_validation is True


def test_missing_required_validation_blocks():
    vs = BaselineValidationSummary().build(validation_results={
        "unit_tests": {"passed": True}})  # safety/claimguard missing
    assert vs.required_missing
    assert vs.blocks_validation is True


def test_warnings_remain_visible():
    vs = BaselineValidationSummary().build(validation_results={
        "unit_tests": {"passed": True}, "safety_tests": {"passed": True},
        "claimguard": {"safe": True}, "safety_invariants": {"passed": True},
        "mini_soak": {"warnings": True}})
    assert vs.has_warnings is True
    d = vs.to_dict()
    assert d["statuses"]["mini_soak"] == ValidationStatus.PASSED_WITH_WARNINGS


def test_passing_does_not_prove_claims():
    vs = BaselineValidationSummary().build(validation_results={
        "unit_tests": {"passed": True}})
    assert "do not prove scientific claims" in vs.to_dict()["note"]
