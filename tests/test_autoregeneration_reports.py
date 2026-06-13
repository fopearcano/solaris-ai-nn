"""Tests for auto-regeneration reports + ClaimGuard."""

from __future__ import annotations

from solaris_ai_nn.autoregeneration import (
    AutoRegenerationEngine,
    AutoRegenerationReportBuilder,
    RepairPolicy,
)
from solaris_ai_nn.autoregeneration.reports import (
    AUTOREGENERATION_LIMITATIONS,
)
from solaris_ai_nn.governance.compliance import ClaimGuard


def _engine(tmp_path):
    engine = AutoRegenerationEngine(
        state_dir=tmp_path, policy=RepairPolicy(mode="safe_auto_repair"))
    engine.tick({"memory": {"over_budget": ["hot"]},
                 "world_model": {"contradiction_edges": ["a|contradicts|b"]},
                 "mysterium_pressure": 0.97, "state_dir": str(tmp_path)})
    return engine


def test_json_report_generated(tmp_path):
    builder = AutoRegenerationReportBuilder(_engine(tmp_path))
    sections = set(builder.to_dict()["sections"])
    for expected in ("degradation_summary", "diagnostics_run",
                     "repair_policy_mode", "proposed_repairs",
                     "applied_repairs", "refused_repairs", "rollback_events",
                     "memory_hygiene_status", "checkpoint_status",
                     "reference_repair_status", "symbol_hygiene_status",
                     "world_model_hygiene_status", "habit_hygiene_status",
                     "drift_recovery_status", "safety_governance_decisions"):
        assert expected in sections


def test_markdown_generated(tmp_path):
    builder = AutoRegenerationReportBuilder(_engine(tmp_path))
    assert "Auto-regeneration report" in builder.to_markdown()


def test_claim_guard_scans_report(tmp_path):
    builder = AutoRegenerationReportBuilder(_engine(tmp_path))
    assert ClaimGuard().is_safe(builder.to_markdown())


def test_limitations_included(tmp_path):
    builder = AutoRegenerationReportBuilder(_engine(tmp_path))
    md = builder.to_markdown()
    assert AUTOREGENERATION_LIMITATIONS
    assert "never source code" in md


def test_save_runs_claim_guard(tmp_path):
    builder = AutoRegenerationReportBuilder(_engine(tmp_path))
    paths = builder.save(tmp_path / "ar.json", tmp_path / "ar.md")
    assert (tmp_path / "ar.md").exists()
    assert paths["claim_guard"]["safe"] is True
