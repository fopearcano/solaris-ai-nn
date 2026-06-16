"""Alpha <-> Scientific Claims: available path runs; unavailable -> placeholder."""

from __future__ import annotations

from solaris_ai_nn.alpha_system import AlphaResearchOrchestrator


def test_claims_available_path(tmp_path):
    orch = AlphaResearchOrchestrator(state_dir=str(tmp_path), max_ticks=25)
    orch.run()
    step = orch.plan.get("claim_summary")
    # Scientific Claims exists in this repo -> the demo-safe call runs.
    assert step is not None
    assert step.status in ("completed", "skipped")


def test_claims_unavailable_placeholder(tmp_path):
    orch = AlphaResearchOrchestrator(state_dir=str(tmp_path), max_ticks=25)
    orch.build_registry()
    orch.registry.get("scientific_claims").status = "missing"
    orch.initialize()
    orch.run_doctor()
    from solaris_ai_nn.alpha_system.artifact_index import (
        AlphaArtifactIndex, AlphaArtifactKind)
    orch.artifact_index = AlphaArtifactIndex(state_root=str(tmp_path))
    orch.plan = __import__(
        "solaris_ai_nn.alpha_system.demo_plan", fromlist=["AlphaDemoPlan"]
    ).AlphaDemoPlan.build()
    step = orch.plan.get("claim_summary")
    orch._run_claims_step(step)
    assert step.status == "skipped"
    assert "unavailable" in step.detail.lower()
