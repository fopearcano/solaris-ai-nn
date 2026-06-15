"""ModuleInventory: generated; missing marked unavailable; safety marked."""

from __future__ import annotations

from solaris_ai_nn.architecture_evolution import (
    ModuleInventory,
    ModuleInventoryEntry,
)


def test_inventory_generated():
    inv = ModuleInventory()
    snap = inv.snapshot()
    assert snap["module_count"] >= 20
    assert "conscience" in inv.entries
    assert "research_lab" in inv.entries


def test_missing_module_marked_unavailable():
    inv = ModuleInventory()
    # Inject a known-missing package and confirm it is marked, not ignored.
    inv.register(ModuleInventoryEntry(
        module_name="ghost", package_path="solaris_ai_nn.ghost",
        available=False, lifecycle_status="unavailable",
        known_issues=["package not importable"]))
    assert "ghost" in inv.unavailable_modules()
    assert inv.get("ghost").available is False


def test_safety_critical_module_marked():
    inv = ModuleInventory()
    crit = inv.safety_critical_modules()
    for m in ("ego", "governance", "motor_membrane", "safety_invariants",
              "conscience"):
        assert m in crit
    assert inv.get("ego").safety_critical is True


def test_attach_evidence():
    inv = ModuleInventory()
    inv.attach_evidence("world_model", research=["research:world_model"])
    assert "research:world_model" in inv.get("world_model").research_evidence_refs


def test_known_packages_available():
    inv = ModuleInventory()
    # The core packages this prompt depends on are importable.
    for m in ("research_lab", "evaluation", "conscience", "inner_map"):
        assert inv.get(m).available is True
