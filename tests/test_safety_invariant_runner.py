"""SafetyInvariantRunner: fast/full runs; fail-closed on missing evidence."""

from __future__ import annotations

from solaris_ai_nn.safety_invariants import (
    InvariantStatus,
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


def test_fast_check_runs():
    runner = SafetyInvariantRunner(registry=SafetyInvariantRegistry())
    bundle = runner.run_fast(_healthy())
    assert bundle.scope == "fast"
    assert bundle.passed_count > 0
    assert bundle.failed_count == 0


def test_full_check_runs():
    runner = SafetyInvariantRunner(registry=SafetyInvariantRegistry())
    bundle = runner.run_full(_healthy())
    assert bundle.scope == "full"
    assert len(bundle.results) == len(
        SafetyInvariantRegistry().all_invariants())


def test_missing_critical_evidence_fail_closed():
    # An empty context -> escalating invariants are inconclusive (never pass).
    runner = SafetyInvariantRunner(registry=SafetyInvariantRegistry())
    bundle = runner.run_fast({})
    assert bundle.inconclusive_count > 0
    assert bundle.passed_count == 0 or all(
        r.evidence_refs for r in bundle.results if r.passed)


def test_real_world_leak_is_critical_failure():
    runner = SafetyInvariantRunner(registry=SafetyInvariantRegistry())
    bundle = runner.run_fast({"motor_membrane": {"real_world_authority": True,
                                                 "firewall_enabled": True}})
    assert len(bundle.critical_failures) >= 1


def test_run_for_module():
    runner = SafetyInvariantRunner(registry=SafetyInvariantRegistry())
    bundle = runner.run_for_module("motor_membrane", _healthy())
    assert bundle.scope == "module:motor_membrane"
    assert bundle.results


def test_runner_does_not_mutate_context():
    runner = SafetyInvariantRunner(registry=SafetyInvariantRegistry())
    ctx = _healthy()
    import copy
    snapshot = copy.deepcopy(ctx)
    runner.run_full(ctx)
    assert ctx == snapshot
