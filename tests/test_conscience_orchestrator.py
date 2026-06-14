"""Conscience orchestrator: the one runtime, bounded, no module sovereign."""

from __future__ import annotations

from solaris_ai_nn.conscience import (
    ConscienceOrchestrator,
    RunContext,
    RunMode,
    ScenarioProfileRegistry,
)


def _ctx(tmp_path, **kw):
    base = dict(mode=RunMode.SHORT_DEMO, state_dir=str(tmp_path),
                max_steps=15,
                enabled_modules=["bridge", "ecology", "world_model",
                                 "homeostasis", "executive", "governance",
                                 "ops"])
    base.update(kw)
    return RunContext(**base)


def test_run_is_bounded_and_clean(tmp_path):
    orch = ConscienceOrchestrator()
    orch.configure(_ctx(tmp_path))
    orch.initialize()
    out = orch.run()
    assert out["completed"] is True
    assert orch.step_count == 15
    assert orch.stopped is True  # safe shutdown after completion


def test_spine_actually_drives_stimulus_push_reaction(tmp_path):
    orch = ConscienceOrchestrator()
    orch.configure(_ctx(tmp_path))
    orch.initialize()
    orch.run()
    counts = orch.summary()["counts"]
    assert counts.get("stimulus", 0) > 0
    assert counts.get("push", 0) > 0
    assert counts.get("reaction", 0) > 0


def test_no_executive_means_no_action_suggestion(tmp_path):
    orch = ConscienceOrchestrator()
    orch.configure(_ctx(tmp_path, enabled_modules=["bridge", "ecology",
                                                   "governance"]))
    orch.initialize()
    orch.run()
    assert orch.summary()["counts"].get("action_suggestion", 0) == 0


def test_partial_config_does_not_crash(tmp_path):
    # Enable a module that is unavailable alongside real ones.
    ctx = _ctx(tmp_path, enabled_modules=["bridge", "ecology", "governance",
                                          "does_not_exist"])
    orch = ConscienceOrchestrator()
    orch.configure(ctx)
    init = orch.initialize()
    assert init["initialized"] is True
    orch.run()
    assert orch.step_count == 15


def test_unbounded_without_approval_refused(tmp_path):
    ctx = _ctx(tmp_path, max_steps=None, max_duration_s=None)
    orch = ConscienceOrchestrator()
    orch.configure(ctx)
    init = orch.initialize()
    assert init["initialized"] is False
    assert orch.refusal_reasons


def test_emergency_stop_halts_run(tmp_path):
    orch = ConscienceOrchestrator()
    orch.configure(_ctx(tmp_path, max_steps=50))
    orch.initialize()
    orch.step()
    orch.request_emergency_stop()
    orch.step()  # detects emergency and shuts down
    assert orch.stopped is True


def test_pause_resume(tmp_path):
    orch = ConscienceOrchestrator()
    orch.configure(_ctx(tmp_path))
    orch.initialize()
    orch.pause()
    assert orch.step()["ran"] is False
    orch.resume()
    assert orch.step()["ran"] is True


def test_plan_only_starts_no_run(tmp_path):
    profile = ScenarioProfileRegistry().require("month_scale_plan")
    profile.run_context.state_dir = str(tmp_path)
    orch = ConscienceOrchestrator(governance_approved=True)
    orch.configure(profile)
    orch.initialize()
    out = orch.run()
    assert out.get("plan_only") is True
    assert orch.step_count == 0


def test_summary_declares_no_sovereign_module(tmp_path):
    orch = ConscienceOrchestrator()
    orch.configure(_ctx(tmp_path))
    orch.initialize()
    assert "no module is sovereign" in orch.summary()["authority_note"]


def test_snapshot_has_all_subsystems(tmp_path):
    orch = ConscienceOrchestrator()
    orch.configure(_ctx(tmp_path))
    orch.initialize()
    orch.step()
    snap = orch.snapshot()
    for key in ("spine", "bus", "registry", "lifecycle", "scheduler",
                "safety"):
        assert key in snap
