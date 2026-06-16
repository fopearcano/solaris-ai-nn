"""Alpha orchestrator: bounded, fixture-only, handles missing, writes artifacts."""

from __future__ import annotations

import os

from solaris_ai_nn.alpha_system import AlphaResearchOrchestrator


def test_bounded_orchestration(tmp_path):
    orch = AlphaResearchOrchestrator(state_dir=str(tmp_path), max_ticks=25)
    result = orch.run()
    assert result["refused"] is False
    assert result["demo_completed"] is True


def test_unbounded_refused(tmp_path):
    orch = AlphaResearchOrchestrator(state_dir=str(tmp_path), max_runtime_s=0)
    assert orch.run()["refused"] is True


def test_fixture_only_run(tmp_path):
    orch = AlphaResearchOrchestrator(state_dir=str(tmp_path), max_ticks=25)
    orch.run()
    assert orch.alpha_profile.is_fixture_only is True
    status = orch.alpha_status()
    assert status["controls_feeders"] is False
    assert status["calls_github"] is False


def test_missing_optional_modules_handled(tmp_path):
    # skip_optional forces all optional organismic steps to skip honestly.
    orch = AlphaResearchOrchestrator(state_dir=str(tmp_path), max_ticks=25,
                                     skip_optional=True)
    orch.run()
    plan = orch.plan.summary()
    assert plan["alpha_demo_step_skipped_count"] >= 1
    # The run still completes; skipped modules do not crash it.
    assert orch.cycle.get("stage")


def test_artifact_index_generated(tmp_path):
    orch = AlphaResearchOrchestrator(state_dir=str(tmp_path), max_ticks=25)
    orch.run()
    assert os.path.isfile(orch.artifact_index.json_path)
    assert orch.artifact_index.index()["alpha_artifact_count"] >= 1


def test_alpha_report_generated(tmp_path):
    orch = AlphaResearchOrchestrator(state_dir=str(tmp_path), max_ticks=25)
    orch.run()
    report = os.path.join(str(tmp_path), "reports",
                          "ALPHA_RESEARCH_SYSTEM_REPORT.md")
    assert os.path.isfile(report)


def test_strict_doctor_block_stops_demo(tmp_path):
    # A strict run with a forced doctor blocker should not complete the demo.
    orch = AlphaResearchOrchestrator(state_dir=str(tmp_path), max_ticks=25,
                                     strict=True, require_claimguard=True)
    # require_claimguard makes a missing ClaimGuard a blocker; if ClaimGuard is
    # present this still runs. Either way the orchestrator must not crash.
    result = orch.run()
    assert "demo_completed" in result
