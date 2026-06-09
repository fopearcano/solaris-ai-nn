"""Tests for the BoundaryRegistry."""

from __future__ import annotations

from solaris_ai_nn.inner_map.boundaries import BoundaryRegistry


def test_lists_hard_and_soft_boundaries():
    reg = BoundaryRegistry()
    names = {b.name for b in reg.list_boundaries()}
    assert "cpu_only" in names
    assert "no_heavy_ml_frameworks" in names
    assert "action_authority_suggest_only" in names
    kinds = {b.kind for b in reg.list_boundaries()}
    assert kinds == {"hard", "soft"}


def test_to_dict_has_hard_and_soft():
    d = BoundaryRegistry().to_dict()
    assert "hard" in d and "soft" in d
    assert any(b["name"] == "cpu_only" for b in d["hard"])
    assert any(b["name"] == "reservoir_size" for b in d["soft"])


def test_detects_unbounded_run_violation():
    reg = BoundaryRegistry()
    violations = reg.check_violation({"unbounded": True, "explicitly_continuous": False})
    assert any(v.boundary == "no_unbounded_run_unless_requested" for v in violations)
    # Explicitly-requested continuous is allowed (no violation).
    ok = reg.check_violation({"unbounded": True, "explicitly_continuous": True})
    assert not any(v.boundary == "no_unbounded_run_unless_requested" for v in ok)


def test_detects_action_authority_violation():
    reg = BoundaryRegistry()
    violations = reg.check_violation({"action_committed": True})
    assert any(v.boundary == "action_authority_suggest_only" for v in violations)
    assert all(v.kind in ("hard", "soft") for v in violations)


def test_clean_state_has_no_violations():
    reg = BoundaryRegistry()
    assert reg.check_violation({"unbounded": False, "action_committed": False}) == []
