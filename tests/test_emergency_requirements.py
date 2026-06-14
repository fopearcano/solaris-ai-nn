"""EmergencyRequirementSet: physical kill switch + deadman timer included."""

from __future__ import annotations

from solaris_ai_nn.pilot4_planning import EmergencyRequirementSet


def test_physical_kill_switch_requirement_included():
    em = EmergencyRequirementSet()
    assert em.has_requirement("physical_kill_switch")
    assert "physical_kill_switch" in em.physical_requirements()


def test_deadman_timer_requirement_included():
    em = EmergencyRequirementSet()
    assert em.has_requirement("deadman_timer")
    assert "deadman_timer" in em.physical_requirements()


def test_software_emergency_stop_present():
    em = EmergencyRequirementSet()
    assert em.has_requirement("software_emergency_stop")
    assert em.has_requirement("action_rate_limiter")
    assert em.has_requirement("disable_external_authority_on_restart")


def test_physical_requirements_are_spec_only():
    em = EmergencyRequirementSet()
    for r in em.requirements:
        if r.physical:
            assert r.spec_only is True
    note = em.snapshot()["note"]
    assert "internal/software" in note
