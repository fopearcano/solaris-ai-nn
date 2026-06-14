"""Pilot-1 <-> Auto-regeneration: budget warnings drive hygiene; events logged."""

from __future__ import annotations

from solaris_ai_nn.autoregeneration import AutoRegenerationEngine, RepairPolicy
from solaris_ai_nn.pilot1 import (
    DailyReviewBuilder,
    ResourceBudget,
    ResourceBudgetMonitor,
    RetentionPolicy,
)


def test_resource_warning_requests_hygiene(tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    (state / "big").write_text("z" * (300 * 1024))
    mon = ResourceBudgetMonitor(budget=ResourceBudget(max_disk_mb=0.01),
                                state_dir=str(state))
    mon.estimate()
    request = mon.hygiene_request()
    assert request is not None
    assert request.get("memory_bloat") is True


def test_hygiene_request_consumed_by_autoregeneration(tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    (state / "big").write_text("z" * (300 * 1024))
    mon = ResourceBudgetMonitor(budget=ResourceBudget(max_disk_mb=0.01),
                                state_dir=str(state))
    mon.estimate()
    engine = AutoRegenerationEngine(
        state_dir=tmp_path, policy=RepairPolicy(mode="observe_only"))
    # The hygiene request is a valid auto-regeneration context (no crash).
    out = engine.tick(mon.hygiene_request() or {})
    assert isinstance(out, dict)


def test_retention_context_feeds_autoregeneration():
    pol = RetentionPolicy()
    pol.classify("warm.jsonl", age_days=10)
    ctx = pol.autoregeneration_context()
    assert "compress" in ctx


def test_autoregeneration_events_appear_in_daily_review(tmp_path):
    builder = DailyReviewBuilder(base_dir=str(tmp_path))
    review = builder.build(1, {"uptime_ratio": 1.0,
                               "autoregeneration_degradation_count": 3,
                               "structural_change_score": 0.1})
    assert review.autoregeneration_events == 3
    md = builder.render_markdown(review)
    assert "auto-regeneration events: 3" in md
