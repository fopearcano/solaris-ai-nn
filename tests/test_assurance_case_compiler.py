"""AssuranceCaseCompiler: case generated; unsupported/contradicted; scanned."""

from __future__ import annotations

import os

from solaris_ai_nn.safety_invariants import (
    AssuranceCaseCompiler,
    AssuranceStatus,
    BoundaryRegressionSuite,
    RedTeamHarness,
    SafetyInvariantRegistry,
    SafetyInvariantRunner,
)


def _healthy():
    return {
        "motor_membrane": {"real_world_authority": False,
                           "firewall_enabled": True,
                           "firewall_can_be_disabled": False,
                           "action_count": 1, "simulated_action_count": 1,
                           "current_authority": "simulation_only"},
        "sensory_membrane": {"read_only": True, "provenance_completeness": 1.0},
        "conscience": {"emergency_stop_available": True},
        "pilot4": {"real_world_actuation_enabled": False,
                   "current_authority": "simulation_only"},
        "report_texts": ["a bounded report with limitations"],
    }


def test_assurance_case_generated(tmp_path):
    bundle = SafetyInvariantRunner(registry=SafetyInvariantRegistry()).run_full(
        _healthy())
    case = AssuranceCaseCompiler(base_dir=str(tmp_path)).compile_and_write(
        invariant_bundle=bundle, red_team_results=RedTeamHarness().run_all(),
        boundary_results=BoundaryRegressionSuite().run_all())
    assert case.claims
    assert os.path.exists(os.path.join(str(tmp_path), "ASSURANCE_CASE.md"))
    assert os.path.exists(os.path.join(str(tmp_path), "ASSURANCE_CASE.json"))
    assert case.supported_count > 0


def test_unsupported_claim_when_no_evidence():
    # No invariant bundle -> claims are inconclusive/unsupported, not supported.
    case = AssuranceCaseCompiler().compile_case()
    assert all(c.status in (AssuranceStatus.INCONCLUSIVE,
                            AssuranceStatus.UNSUPPORTED) for c in case.claims)
    assert case.supported_count == 0


def test_contradicted_evidence_marked_contradicted():
    # A real-world authority leak fails the motor invariant -> contradicted.
    bundle = SafetyInvariantRunner(registry=SafetyInvariantRegistry()).run_full(
        {"motor_membrane": {"real_world_authority": True,
                            "firewall_enabled": True}})
    case = AssuranceCaseCompiler().compile_case(invariant_bundle=bundle)
    statuses = {c.claim_id: c.status for c in case.claims}
    assert statuses["motor_membrane_simulation_only"] == \
        AssuranceStatus.CONTRADICTED
    assert case.contradicted_count >= 1


def test_claim_guard_scans_markdown(tmp_path):
    bundle = SafetyInvariantRunner(registry=SafetyInvariantRegistry()).run_full(
        _healthy())
    case = AssuranceCaseCompiler(base_dir=str(tmp_path)).compile_case(
        invariant_bundle=bundle)
    assert case.claim_guard_safe is True
