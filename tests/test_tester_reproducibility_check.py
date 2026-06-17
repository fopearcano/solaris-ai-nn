"""Reproducibility check: pass, warning, missing-required fail, unsupported-claim fail."""

from __future__ import annotations

from solaris_ai_nn.tester_fixture_spine import (
    GoldenManifestBuilder,
    TesterReproducibilityCheck,
    default_expected_outputs,
)

_SPEC = default_expected_outputs()


def _good_context():
    return {
        "fixture_present": True, "unsafe_quarantined": True,
        "secret_present": False, "membrane_present": True,
        "membrane_impression_count": 16,
        "all_impressions_have_receptor": True,
        "all_impressions_have_source_ref": True,
        "operator_pulse_attenuated": True, "debug_gloss_not_truth": True,
        "human_label_not_truth": True, "source_pressure_present": True,
        "membrane_memory_present": True,
        "observation_distinguishes_diets": True,
        "ontogenesis_ran": True, "ontogenesis_used_impressions": True,
        "semiogenesis_ran": True, "semiogenesis_ancestry_preserved": True,
        "cognition_ran": True, "cognition_ancestry_preserved": True,
        "reports_have_disclaimers": True, "claims_safe": True,
        "raw_bypass_detected": False, "no_external_access": True,
        "fixture_quarantined_count": 1, "blocked": False,
        "fixture_hash": "abc",
    }


def _golden(all_present=True):
    from solaris_ai_nn.tester_fixture_spine.golden_manifest import (
        _GOLDEN_ARTIFACT_TYPES)
    present = {t: True for t, _ in _GOLDEN_ARTIFACT_TYPES} if all_present else {}
    return GoldenManifestBuilder().build(
        profile_id="fixture_tester_v0", fixture_hash="abc",
        present_artifacts=present)


def _present_all():
    from solaris_ai_nn.tester_fixture_spine.golden_manifest import (
        _GOLDEN_ARTIFACT_TYPES)
    return {t: True for t, _ in _GOLDEN_ARTIFACT_TYPES}


def test_pass_case():
    ctx = _good_context()
    ctx["present_artifacts"] = _present_all()
    result = TesterReproducibilityCheck().check(
        context=ctx, expected_spec=_SPEC, golden_manifest=_golden(),
        expected_fixture_hash="abc")
    assert result.status == "pass"
    assert result.fail_count == 0


def test_warning_case_missing_optional():
    ctx = _good_context()
    present = _present_all()
    present["ontogenesis_candidate_summary"] = False
    ctx["present_artifacts"] = present
    result = TesterReproducibilityCheck().check(
        context=ctx, expected_spec=_SPEC, golden_manifest=_golden(),
        expected_fixture_hash="abc")
    assert result.status == "pass_with_warnings"


def test_missing_required_artifact_fails():
    ctx = _good_context()
    present = _present_all()
    present["membrane_report"] = False
    ctx["present_artifacts"] = present
    result = TesterReproducibilityCheck().check(
        context=ctx, expected_spec=_SPEC, golden_manifest=_golden(),
        expected_fixture_hash="abc")
    assert result.status == "fail"
    assert result.fail_count >= 1


def test_unsupported_claim_fails():
    ctx = _good_context()
    ctx["present_artifacts"] = _present_all()
    ctx["claims_safe"] = False
    result = TesterReproducibilityCheck().check(
        context=ctx, expected_spec=_SPEC, golden_manifest=_golden(),
        expected_fixture_hash="abc")
    assert result.status == "fail"
