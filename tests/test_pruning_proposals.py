"""PruningProposalBuilder: proposal generated; safety blocked; no deletion."""

from __future__ import annotations

from solaris_ai_nn.architecture_evolution import (
    PruningImplementationStatus,
    PruningProposalBuilder,
)


def test_pruning_proposal_generated():
    p = PruningProposalBuilder().build("latent", evidence_refs=["r"],
                                       integration_count=2)
    assert p.target_module == "latent"
    assert p.blocked is False
    assert p.plan.rollback_plan
    assert p.operator_review_required is True


def test_safety_critical_pruning_blocked():
    p = PruningProposalBuilder().build("ego", safety_critical=True,
                                       evidence_refs=["r"])
    assert p.blocked is True
    assert "safety-critical" in p.blocked_reason
    assert p.implementation_status == PruningImplementationStatus.NOT_IMPLEMENTED


def test_proposal_does_not_delete_code():
    p = PruningProposalBuilder().build("latent", evidence_refs=["r"])
    assert p.implementation_status in (
        PruningImplementationStatus.PLANNING_ONLY,
        PruningImplementationStatus.EXTERNAL_MANUAL_CHANGE_REQUIRED)
    assert "no code is deleted" in p.to_dict()["note"]


def test_high_integration_proposes_quarantine_first():
    p = PruningProposalBuilder().build("world_model", evidence_refs=["r"],
                                       integration_count=4)
    assert p.quarantine_first is True


def test_build_from_assessment_respects_safety():
    from solaris_ai_nn.architecture_evolution import ModuleLifecycleClassifier

    a = ModuleLifecycleClassifier().classify("ego", safety_critical=True)
    p = PruningProposalBuilder().build_from_assessment(a, safety_critical=True)
    assert p.blocked is True
