"""AblationMatrix: required cases exist; disabled recorded; safety stays on."""

from __future__ import annotations

from solaris_ai_nn.research_lab import AblationMatrix


def test_required_ablations_exist():
    m = AblationMatrix()
    for name in ("full_system", "minimal_spine_only", "no_memory",
                 "no_world_model", "no_proto_language", "no_active_perception",
                 "no_hypothesis_engine", "no_LOGOS", "no_latent_replay",
                 "no_auto_regeneration", "no_homeostasis",
                 "no_sensory_membrane", "no_motor_membrane", "no_synthesis",
                 "safety_only", "nursery_without_sensory",
                 "sensory_without_nursery", "gridworld_without_proto_language",
                 "gridworld_without_hypothesis_engine", "full_minus_one_each"):
        assert name in m.cases, name


def test_disabled_modules_recorded():
    m = AblationMatrix()
    case = m.get("no_proto_language")
    assert "enable_proto_language" in case.disabled
    assert "enable_proto_language" in case.unavailable_modules


def test_missing_module_marked_unavailable():
    m = AblationMatrix()
    case = m.get("no_memory")
    # The disabled module is recorded as unavailable, never silently ignored.
    assert case.to_dict()["unavailable_modules"] == ["enable_memory"]


def test_hard_safety_always_enabled():
    m = AblationMatrix()
    assert m.all_hard_safety_enabled() is True
    for case in m.cases.values():
        assert case.variant.hard_safety_enabled() is True


def test_minimal_spine_disables_cognitive_only():
    m = AblationMatrix()
    case = m.get("minimal_spine_only")
    assert case.variant.hard_safety_enabled() is True
    assert "enable_memory" in case.disabled
