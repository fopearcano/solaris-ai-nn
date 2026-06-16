"""Alpha <-> Research Cycle: available path runs; fallback cycle status works."""

from __future__ import annotations

from solaris_ai_nn.alpha_system import AlphaResearchOrchestrator
from solaris_ai_nn.alpha_system.artifact_index import AlphaArtifactIndex
from solaris_ai_nn.alpha_system.demo_plan import AlphaDemoPlan


def test_research_cycle_available_path(tmp_path):
    orch = AlphaResearchOrchestrator(state_dir=str(tmp_path), max_ticks=25)
    orch.run()
    step = orch.plan.get("cycle_status")
    assert step is not None
    assert step.status in ("completed", "warning")


def test_fallback_cycle_status_works(tmp_path):
    orch = AlphaResearchOrchestrator(state_dir=str(tmp_path), max_ticks=25)
    orch.build_registry()
    orch.registry.get("research_cycle").status = "missing"
    orch.initialize()
    orch.artifact_index = AlphaArtifactIndex(state_root=str(tmp_path))
    orch.plan = AlphaDemoPlan.build()
    step = orch.plan.get("cycle_status")
    orch._run_cycle_step(step)
    # Fallback path produces a warning step (not a crash) with an artifact.
    assert step.status == "warning"
    assert step.artifact_ref


def test_orchestrator_always_has_cycle_status(tmp_path):
    orch = AlphaResearchOrchestrator(state_dir=str(tmp_path), max_ticks=25)
    orch.run()
    # The alpha fallback AlphaCycleStatus is always present in the result.
    assert orch.cycle.get("stage")
    assert orch.cycle.get("next_action")
