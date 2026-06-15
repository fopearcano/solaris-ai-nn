"""Sensorium lab <-> Research Lab + Architecture Evolution integration."""

from __future__ import annotations

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS
from solaris_ai_nn.sensorium_lab import (
    SensoriumDifferentiationRunner,
    default_study_design,
)


def test_research_protocol_consumes_report(tmp_path):
    reg = ExperimentRegistry()
    for name in ("sensorium_differentiation", "human_vs_nonhuman_sensorium",
                 "label_contamination"):
        manifest = reg.build_manifest(name, {"steps": 6,
                                             "state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result.success, result.error
        assert "sensorium_lab" in result.metrics


def test_architecture_proposal_inputs_generated(tmp_path):
    design = default_study_design()
    design.ticks = 40
    runner = SensoriumDifferentiationRunner(state_dir=str(tmp_path / "lab"),
                                            design=design)
    runner.prepare_study(design)
    runner.run_all()
    proposals = runner.architecture_proposals()
    assert proposals
    # Proposals are inputs only; they never trigger code changes.
    assert all("proposal_type" in p and "rationale" in p for p in proposals)


def test_proposals_consumable_by_roadmap(tmp_path):
    from solaris_ai_nn.architecture_evolution import RoadmapCompiler

    design = default_study_design()
    design.ticks = 30
    runner = SensoriumDifferentiationRunner(state_dir=str(tmp_path / "lab"),
                                            design=design)
    runner.prepare_study(design)
    runner.run_all()
    proposals = runner.architecture_proposals()
    recs = [f"{p['proposal_type']}: {p['rationale']}" for p in proposals]
    items = RoadmapCompiler(base_dir=str(tmp_path / "arch")).compile(
        pilot_recommendations=recs)
    assert isinstance(items, list)
