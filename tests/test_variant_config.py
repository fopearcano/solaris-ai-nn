"""SolarisVariantConfig: toggles work; external forbidden; safety locked."""

from __future__ import annotations

import pytest

from solaris_ai_nn.research_lab import SolarisVariantConfig, VariantAuthority


def test_module_toggles_work():
    v = SolarisVariantConfig.full().disable("enable_proto_language",
                                            "enable_LOGOS")
    assert "enable_proto_language" in v.disabled_modules
    assert "enable_LOGOS" in v.disabled_modules
    assert v.enable_memory is True


def test_external_authority_forbidden():
    with pytest.raises(ValueError):
        SolarisVariantConfig(authority=VariantAuthority.FORBIDDEN_EXTERNAL)


def test_hard_safety_cannot_be_disabled_for_membrane_profiles():
    with pytest.raises(ValueError):
        SolarisVariantConfig(enable_sensory_membrane=True,
                             enable_safety_invariants=False)
    with pytest.raises(ValueError):
        SolarisVariantConfig(enable_motor_membrane=True,
                             enable_governance=False)


def test_cannot_disable_hard_safety_toggle_via_disable():
    with pytest.raises(ValueError):
        SolarisVariantConfig.full().disable("enable_safety_invariants")


def test_minimal_disables_cognitive_keeps_safety():
    v = SolarisVariantConfig.minimal()
    assert v.hard_safety_enabled() is True
    assert v.enable_memory is False and v.enable_LOGOS is False


def test_roundtrip():
    v = SolarisVariantConfig.full().disable("enable_memory")
    d = v.to_dict()
    assert SolarisVariantConfig.from_dict(d).enable_memory is False
