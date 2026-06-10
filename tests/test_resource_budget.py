"""Tests for the ResourceBudget."""

from __future__ import annotations

from solaris_ai_nn.ops.resource_budget import ResourceBudget, directory_bytes


def test_detects_step_limit():
    budget = ResourceBudget(max_steps=100)
    report = budget.check_budget({"telemetry": {"lifetime_steps": 500}})
    assert not report.within
    assert any("steps" in v for v in report.violations)
    assert not budget.within_budget()


def test_detects_artifact_byte_limit(tmp_path):
    (tmp_path / "big.bin").write_bytes(b"x" * 2048)
    budget = ResourceBudget(max_artifact_bytes=1024)
    report = budget.check_budget({"telemetry": {}}, artifact_dir=tmp_path)
    assert any("artifact bytes" in v for v in report.violations)
    assert report.usage["artifact_bytes"] >= 2048


def test_within_budget_when_clean(tmp_path):
    budget = ResourceBudget()
    report = budget.check_budget(
        {"telemetry": {"lifetime_steps": 10}, "runtime_s": 1.0},
        artifact_dir=tmp_path)
    assert report.within
    assert budget.violations() == []
    assert "limits" in budget.to_dict()


def test_handles_missing_resource_module_gracefully(monkeypatch):
    import solaris_ai_nn.ops.resource_budget as rb

    monkeypatch.setattr(rb, "_resource", None)
    report = ResourceBudget().check_budget({"telemetry": {}})
    assert "max_rss_kb" not in report.usage  # skipped, not crashed


def test_directory_bytes_missing_dir():
    assert directory_bytes("/nonexistent/path/xyz") == 0
