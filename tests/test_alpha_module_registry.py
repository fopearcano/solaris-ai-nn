"""Alpha module registry: builds, warns, blocks, no crash on missing."""

from __future__ import annotations

from solaris_ai_nn.alpha_system import (
    AlphaModuleRegistry,
    AlphaModuleStatus,
)


def test_registry_builds():
    registry = AlphaModuleRegistry.build()
    assert registry.records
    idx = registry.index()
    assert idx["alpha_module_count"] == len(registry.records)
    # All real package modules should be importable in this repo.
    assert idx["alpha_available_module_count"] >= 1


def test_missing_optional_module_warns():
    registry = AlphaModuleRegistry.build()
    rec = registry.get("live_field")
    assert rec is not None
    rec.status = AlphaModuleStatus.OPTIONAL_MISSING
    # Optional missing does not block alpha.
    assert rec.blocks_alpha is False
    assert rec in registry.optional_missing()


def test_missing_required_module_blocks_command():
    registry = AlphaModuleRegistry.build()
    rec = registry.get("evaluation")  # required
    assert rec is not None
    rec.status = AlphaModuleStatus.MISSING
    assert rec.blocks_alpha is True
    assert rec in registry.blocking_alpha()


def test_no_crash_on_missing_module():
    # A broken/missing submodule probe returns a status, never raises.
    status, detail = AlphaModuleRegistry._probe("definitely_not_a_module", True)
    assert status in AlphaModuleStatus.ALL


def test_registry_inspectable():
    d = AlphaModuleRegistry.build().to_dict()
    assert "modules" in d
    assert all("status" in m for m in d["modules"])
