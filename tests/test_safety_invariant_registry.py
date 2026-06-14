"""SafetyInvariantRegistry: built-ins registered; duplicates rejected; coverage."""

from __future__ import annotations

import pytest

from solaris_ai_nn.safety_invariants import (
    InvariantCategory,
    SafetyInvariant,
    SafetyInvariantRegistry,
)


def test_builtin_invariants_registered():
    reg = SafetyInvariantRegistry()
    assert len(reg.all_invariants()) >= 20
    cats = {i.category for i in reg.all_invariants()}
    assert InvariantCategory.NO_REAL_WORLD_ACTUATION in cats
    assert InvariantCategory.READ_ONLY_SENSORY_BOUNDARY in cats


def test_duplicate_ids_rejected():
    reg = SafetyInvariantRegistry()
    existing = reg.all_invariants()[0]
    with pytest.raises(ValueError):
        reg.register(existing)


def test_coverage_computed():
    reg = SafetyInvariantRegistry()
    cov = reg.coverage()
    assert cov["invariant_count"] == len(reg.all_invariants())
    assert 0.0 <= cov["category_coverage_ratio"] <= 1.0
    assert cov["category_coverage_ratio"] > 0.5


def test_for_module_filters():
    reg = SafetyInvariantRegistry()
    motor = reg.for_module("motor_membrane")
    assert motor
    assert all("motor_membrane" in i.applies_to_modules or
               not i.applies_to_modules for i in motor)


def test_module_specific_registration():
    reg = SafetyInvariantRegistry()
    before = len(reg.all_invariants())
    reg.register_module_invariant(SafetyInvariant(
        category=InvariantCategory.NO_HIDDEN_FAILURE, title="custom",
        applies_to_modules=["custom_mod"]))
    assert len(reg.all_invariants()) == before + 1
    assert reg.for_module("custom_mod")


def test_persist(tmp_path):
    path = SafetyInvariantRegistry().persist(str(tmp_path))
    import os
    assert os.path.exists(path)
