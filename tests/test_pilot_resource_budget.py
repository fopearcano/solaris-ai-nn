"""Pilot-1 resource budget: stdlib sizing, projection, over-budget warning."""

from __future__ import annotations

from solaris_ai_nn.pilot1 import ResourceBudget, ResourceBudgetMonitor


def test_directory_size_computed(tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    (state / "a.jsonl").write_text("x" * 1024)
    mon = ResourceBudgetMonitor(state_dir=str(state))
    est = mon.estimate()
    assert est.state_bytes >= 1024
    assert est.total_mb > 0


def test_projection_estimated(tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    (state / "a.jsonl").write_text("y" * 4096)
    mon = ResourceBudgetMonitor(state_dir=str(state))
    est = mon.estimate()
    assert est.projected_30d_mb >= 0.0
    assert est.projected_365d_mb >= est.projected_30d_mb


def test_over_budget_warning(tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    (state / "big").write_text("z" * (200 * 1024))
    mon = ResourceBudgetMonitor(budget=ResourceBudget(max_disk_mb=0.01),
                                state_dir=str(state))
    est = mon.estimate()
    assert est.over_budget is True
    assert est.warnings


def test_requests_hygiene_when_over_budget(tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    (state / "big").write_text("z" * (200 * 1024))
    mon = ResourceBudgetMonitor(budget=ResourceBudget(max_disk_mb=0.01),
                                state_dir=str(state))
    mon.estimate()
    assert mon.requests_hygiene() is True
    req = mon.hygiene_request()
    assert req and req.get("log_rotation_requested")


def test_no_psutil_dependency():
    import solaris_ai_nn.pilot1.resource_budget as rb_module

    with open(rb_module.__file__, encoding="utf-8") as fh:
        assert "import psutil" not in fh.read()
