"""Alpha <-> Independent Review: available path runs; unavailable -> placeholder."""

from __future__ import annotations

from solaris_ai_nn.alpha_system import AlphaResearchOrchestrator
from solaris_ai_nn.alpha_system.artifact_index import AlphaArtifactIndex
from solaris_ai_nn.alpha_system.demo_plan import AlphaDemoPlan


def test_review_available_path(tmp_path):
    orch = AlphaResearchOrchestrator(state_dir=str(tmp_path), max_ticks=25)
    orch.run()
    step = orch.plan.get("review_pack")
    assert step is not None
    assert step.status in ("completed", "skipped")


def test_review_unavailable_placeholder(tmp_path):
    orch = AlphaResearchOrchestrator(state_dir=str(tmp_path), max_ticks=25)
    orch.build_registry()
    orch.registry.get("independent_review").status = "missing"
    orch.initialize()
    orch.artifact_index = AlphaArtifactIndex(state_root=str(tmp_path))
    orch.plan = AlphaDemoPlan.build()
    step = orch.plan.get("review_pack")
    orch._run_review_step(step)
    assert step.status == "skipped"
    assert "unavailable" in step.detail.lower()
