"""ArchitectureEvolutionSafetyValidator: source/git/delete/claims blocked."""

from __future__ import annotations

from solaris_ai_nn.architecture_evolution import (
    ArchitectureEvolutionSafetyValidator,
    HARD_RULES,
)


def test_capabilities_all_false():
    v = ArchitectureEvolutionSafetyValidator
    assert v.can_modify_source() is False
    assert v.can_run_git() is False
    assert v.can_auto_delete() is False
    assert v.can_prune_safety_critical() is False
    assert v.can_implement_recommendation() is False


def test_source_modification_blocked():
    v = ArchitectureEvolutionSafetyValidator()
    assert v.validate_operation("modify source file").safe is False
    assert v.validate_operation("rewrite import statements").safe is False


def test_git_operation_blocked():
    v = ArchitectureEvolutionSafetyValidator()
    assert v.validate_operation("git commit -a").safe is False
    assert v.validate_operation("rewrite history with git rebase").safe is False


def test_automatic_deletion_blocked():
    v = ArchitectureEvolutionSafetyValidator()
    assert v.validate_operation("auto delete module").safe is False
    assert v.validate_operation("remove package latent").safe is False


def test_safety_critical_pruning_blocked():
    v = ArchitectureEvolutionSafetyValidator()
    assert v.validate_pruning("ego", safety_critical=True).safe is False
    assert v.validate_pruning("latent", safety_critical=False).safe is True


def test_recommendation_to_implementation_blocked():
    v = ArchitectureEvolutionSafetyValidator()
    assert v.validate_not_implementation(
        "implement the prune change now").safe is False


def test_real_world_actuation_blocked():
    v = ArchitectureEvolutionSafetyValidator()
    assert v.validate_operation("enable real_world actuation").safe is False


def test_hiding_negative_evidence_blocked():
    v = ArchitectureEvolutionSafetyValidator()
    assert v.validate_negative_evidence_visible(hidden=True).safe is False


def test_unsupported_claims_blocked():
    v = ArchitectureEvolutionSafetyValidator()
    assert v.validate_claim_text("the system is a self-improving mind").safe \
        is False
    assert v.validate_claim_text("a planning artifact for review").safe is True


def test_hard_rules_present():
    assert "no source-code modification" in HARD_RULES
    assert "no Git operations" in HARD_RULES
    assert "no converting recommendation into implementation" in HARD_RULES
