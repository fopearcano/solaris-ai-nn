"""Module registry: detection, enablement, missing modules, dependencies."""

from __future__ import annotations

from solaris_ai_nn.conscience import (
    ConscienceModuleRegistry,
    ModuleCapability,
    ModuleDescriptor,
)


def test_detect_marks_available_modules():
    reg = ConscienceModuleRegistry().detect(["bridge", "governance"])
    assert "bridge" in reg.available()
    assert "governance" in reg.available()
    assert "bridge" in reg.enabled()


def test_governance_is_critical():
    reg = ConscienceModuleRegistry().detect([])
    assert reg.modules["governance"].critical is True


def test_missing_is_enabled_but_unavailable():
    reg = ConscienceModuleRegistry()
    reg.detect(["bridge"])
    # Force an enabled-but-unavailable module.
    reg.register("ghost", ModuleDescriptor(
        name="ghost", package_path="nope.nope",
        capability=ModuleCapability.MEMORY, enabled=True, available=False))
    assert "ghost" in reg.missing()


def test_validate_dependencies_reports_unmet():
    reg = ConscienceModuleRegistry()
    reg.register("child", ModuleDescriptor(
        name="child", package_path="x", capability=ModuleCapability.MEMORY,
        enabled=True, available=True, dependencies=["absent"]))
    unmet = reg.validate_dependencies()
    assert unmet.get("child") == ["absent"]


def test_topology_has_nodes_and_edges():
    reg = ConscienceModuleRegistry().detect(["world_model"])
    topo = reg.topology()
    assert any(n["name"] == "world_model" for n in topo["nodes"])
    assert isinstance(topo["edges"], list)


def test_snapshot_shape():
    reg = ConscienceModuleRegistry().detect(["bridge"])
    snap = reg.snapshot()
    assert "enabled" in snap and "available" in snap and "missing" in snap
