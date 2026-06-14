"""ActuatorTaxonomy: categories exist; external prohibited; tiers serialize."""

from __future__ import annotations

from solaris_ai_nn.pilot4_planning import (
    ActuatorCategory,
    ActuatorClass,
    ActuatorRiskTier,
    ActuatorTaxonomy,
)


def test_categories_exist():
    for cat in ("internal_state_action", "simulation_action", "dry_run_action",
                "read_only_observation", "file_write_action", "network_action",
                "browser_action", "os_action", "robotic_action",
                "device_action", "financial_action", "communication_action",
                "physical_world_action", "unknown_action"):
        assert cat in ActuatorCategory.ALL


def test_external_categories_prohibited_in_pilot4():
    t = ActuatorTaxonomy()
    for cat in ActuatorCategory.EXTERNAL:
        c = t.classify(cat)
        assert c.prohibited_in_pilot4 is True
        assert c.risk_tier == ActuatorRiskTier.PROHIBITED
        assert t.is_prohibited_in_pilot4(cat) is True


def test_internal_categories_not_prohibited():
    t = ActuatorTaxonomy()
    assert t.is_prohibited_in_pilot4(
        ActuatorCategory.SIMULATION_ACTION) is False
    assert t.classify(ActuatorCategory.SIMULATION_ACTION).risk_tier == \
        ActuatorRiskTier.SIMULATION_ONLY


def test_risk_tiers_serialize():
    c = ActuatorClass(ActuatorCategory.NETWORK_ACTION, "network")
    d = c.to_dict()
    assert d["risk_tier"] == ActuatorRiskTier.PROHIBITED
    assert set(ActuatorRiskTier.ALL) >= {"safe_internal", "simulation_only",
                                         "prohibited", "unknown"}


def test_snapshot_lists_prohibited():
    snap = ActuatorTaxonomy().snapshot()
    assert set(snap["prohibited_categories"]) == set(ActuatorCategory.EXTERNAL)
