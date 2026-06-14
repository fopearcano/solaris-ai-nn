"""HardwareIsolationPlan: requirements generated; no hardware access."""

from __future__ import annotations

from solaris_ai_nn.pilot4_planning import HardwareIsolationPlan


def test_requirements_generated():
    plan = HardwareIsolationPlan()
    for name in ("separate_sandbox_machine", "no_direct_network_by_default",
                 "physical_kill_switch", "power_isolation",
                 "actuator_simulator_first", "manual_enable_switch",
                 "hardware_whitelist", "one_action_at_a_time", "rate_limiter",
                 "external_supervisor", "independent_logger"):
        assert plan.has_requirement(name), name


def test_no_hardware_access_performed():
    plan = HardwareIsolationPlan()
    assert plan.hardware_connected is False
    assert plan.hardware_scanned is False
    snap = plan.snapshot()
    assert snap["hardware_connected"] is False
    assert snap["hardware_scanned"] is False
    assert "no hardware is connected" in snap["note"]
