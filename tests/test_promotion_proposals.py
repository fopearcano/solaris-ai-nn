"""ModuleRoleChangePlan: promotion/demotion generated; role change needs ADR."""

from __future__ import annotations

from solaris_ai_nn.architecture_evolution import ModuleRoleChangePlan


def test_promotion_proposal_generated():
    plan = ModuleRoleChangePlan()
    prop = plan.propose_promotion("world_model", evidence_refs=["r"],
                                  reproducible_benefit=True,
                                  low_safety_risk=True, stable_integration=True)
    assert prop is not None
    assert prop.to_role == "core_keep"
    assert prop.requires_adr is True


def test_promotion_requires_criteria():
    plan = ModuleRoleChangePlan()
    # Without reproducible benefit, no promotion is proposed.
    assert plan.propose_promotion("x", reproducible_benefit=False) is None


def test_demotion_proposal_generated():
    plan = ModuleRoleChangePlan()
    prop = plan.propose_demotion("latent", evidence_refs=["r"],
                                 high_overhead=True, weak_evidence=True)
    assert prop is not None
    assert prop.to_role == "experimental_keep"
    assert "high overhead" in prop.reasons


def test_role_change_requires_adr():
    plan = ModuleRoleChangePlan()
    prom = plan.propose_promotion("world_model", reproducible_benefit=True)
    dem = plan.propose_demotion("latent", high_overhead=True)
    assert prom.requires_adr is True
    assert dem.requires_adr is True
    assert "not metaphysical importance" in prom.to_dict()["note"]
    assert "not deletion" in dem.to_dict()["note"]


def test_no_demotion_without_reason():
    plan = ModuleRoleChangePlan()
    assert plan.propose_demotion("x") is None
