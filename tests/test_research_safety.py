"""ResearchLabSafetyValidator: blocks action/authority/disable/delete/claims."""

from __future__ import annotations

from solaris_ai_nn.research_lab import HARD_RULES, ResearchLabSafetyValidator


def test_capabilities_all_false():
    v = ResearchLabSafetyValidator
    assert v.can_act_real_world() is False
    assert v.can_hold_external_authority() is False
    assert v.can_run_network_browser_os_device() is False
    assert v.can_start_long_unbounded_run() is False
    assert v.can_disable_hard_safety() is False
    assert v.can_delete_unfavorable_results() is False


def test_real_world_action_blocked():
    v = ResearchLabSafetyValidator()
    assert v.validate_operation("actuate real world device").safe is False
    assert v.validate_operation("http network request").safe is False
    assert v.validate_operation("run shell").safe is False


def test_external_authority_blocked():
    v = ResearchLabSafetyValidator()
    assert v.validate_authority("forbidden_external").safe is False
    assert v.validate_authority("simulation_only").safe is True


def test_disabling_hard_safety_blocked():
    v = ResearchLabSafetyValidator()

    class _V:
        enable_sensory_membrane = True
        enable_motor_membrane = False
        enable_safety_invariants = False
        enable_governance = True

    assert v.validate_no_disable_hard_safety(_V()).safe is False


def test_deleting_negative_result_blocked():
    v = ResearchLabSafetyValidator()
    assert v.validate_result_deletion(favorable=False).safe is False
    assert v.validate_negative_effect_visible(hidden=True).safe is False


def test_consciousness_benchmark_blocked():
    v = ResearchLabSafetyValidator()
    assert v.validate_metric_name("consciousness_score").safe is False
    assert v.validate_metric_name("sentience_level").safe is False
    assert v.validate_metric_name("prediction_accuracy").safe is True


def test_long_unbounded_run_blocked():
    v = ResearchLabSafetyValidator()
    assert v.validate_run_bounds(max_steps=None).safe is False
    assert v.validate_run_bounds(max_steps=20, mode="continuous_explicit").safe \
        is False
    assert v.validate_run_bounds(max_steps=20).safe is True


def test_claim_text_blocked():
    v = ResearchLabSafetyValidator()
    assert v.validate_claim_text("the system is conscious").safe is False
    assert v.validate_claim_text("a bounded benchmark run").safe is True


def test_hard_rules_present():
    assert "no external authority" in HARD_RULES
    assert "no deleting unfavorable results" in HARD_RULES
    assert "no benchmark score named consciousness/life/sentience" in HARD_RULES
