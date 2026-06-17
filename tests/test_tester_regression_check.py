"""Regression check: no regression, membrane-missing, disclaimer-missing, claim."""

from __future__ import annotations

from solaris_ai_nn.tester_fixture_spine import (
    GoldenManifestBuilder,
    TesterRegressionCheck,
)


def _golden():
    from solaris_ai_nn.tester_fixture_spine.golden_manifest import (
        _GOLDEN_ARTIFACT_TYPES)
    return GoldenManifestBuilder().build(
        profile_id="fixture_tester_v0", fixture_hash="abc",
        present_artifacts={t: True for t, _ in _GOLDEN_ARTIFACT_TYPES})


def _good():
    from solaris_ai_nn.tester_fixture_spine.golden_manifest import (
        _GOLDEN_ARTIFACT_TYPES)
    return {"membrane_present": True, "membrane_impression_count": 16,
            "raw_bypass_detected": False, "reports_have_disclaimers": True,
            "claims_safe": True, "fixture_quarantined_count": 1,
            "present_artifacts": {t: True for t, _ in _GOLDEN_ARTIFACT_TYPES}}


def test_no_regression_case():
    r = TesterRegressionCheck().check(context=_good(), golden_manifest=_golden())
    assert r["regression_status"] == "no_regression"


def test_membrane_missing_regression_fails():
    ctx = _good()
    ctx["membrane_present"] = False
    ctx["membrane_impression_count"] = 0
    r = TesterRegressionCheck().check(context=ctx, golden_manifest=_golden())
    assert r["regression_status"] == "regression"


def test_safety_disclaimer_missing_fails():
    ctx = _good()
    ctx["reports_have_disclaimers"] = False
    r = TesterRegressionCheck().check(context=ctx, golden_manifest=_golden())
    assert r["regression_status"] == "regression"


def test_unsupported_claim_fails():
    ctx = _good()
    ctx["claims_safe"] = False
    r = TesterRegressionCheck().check(context=ctx, golden_manifest=_golden())
    assert r["regression_status"] == "regression"


def test_no_golden_inconclusive():
    r = TesterRegressionCheck().check(context=_good(), golden_manifest=None)
    assert r["regression_status"] == "inconclusive"
