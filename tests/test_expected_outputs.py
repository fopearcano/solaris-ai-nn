"""Expected outputs: invariants defined, safety invariants, membrane invariants."""

from __future__ import annotations

from solaris_ai_nn.tester_fixture_spine import default_expected_outputs


def test_expected_invariants_defined():
    spec = default_expected_outputs()
    assert spec.artifacts
    assert spec.safety_invariants
    names = {s.name for s in spec.safety_invariants}
    assert "fixture_input_exists" in names


def test_safety_invariants_defined():
    spec = default_expected_outputs()
    names = {s.name for s in spec.safety_invariants}
    assert "no_consciousness_life_agency_claims" in names
    assert "no_raw_event_downstream_bypass" in names
    assert "no_feeder_hardware_network_git_shell_access" in names


def test_membrane_invariants_defined():
    spec = default_expected_outputs()
    names = {s.name for s in spec.safety_invariants}
    assert "membrane_generates_impressions" in names
    assert "every_impression_has_receptor" in names
    assert "every_impression_has_source_event_ref" in names
    assert "operator_pulse_attenuated" in names


def test_evaluate_passes_on_good_context():
    spec = default_expected_outputs()
    ctx = {k: True for s in spec.safety_invariants for k in [s.name]}
    # Provide the predicate-keyed context for a known-good run.
    good = {
        "fixture_present": True, "unsafe_quarantined": True,
        "secret_present": False, "membrane_impression_count": 16,
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
        "fixture_quarantined_count": 1,
    }
    result = spec.evaluate(good)
    assert result["passed"] is True
    assert result["failed_count"] == 0


def test_evaluate_fails_on_claim_violation():
    spec = default_expected_outputs()
    bad = {"fixture_present": True, "claims_safe": False,
           "membrane_impression_count": 16, "fixture_quarantined_count": 1}
    result = spec.evaluate(bad)
    assert result["passed"] is False
