"""Developmental: research protocols exist; Architecture Evolution consumes report."""

from __future__ import annotations

from solaris_ai_nn.architecture_evolution import developmental_revision_proposals
from solaris_ai_nn.developmental_life import LongHorizonDevelopmentalRuntime
from solaris_ai_nn.evaluation.protocols import PROTOCOLS


def _runtime(tmp_path):
    dev = LongHorizonDevelopmentalRuntime(
        state_dir=str(tmp_path / "dev"),
        modules={"perceptual_metabolism": {"source_diet_diversity": 0.1},
                 "perceptual_ontogenesis": {"proto_concept_count": 4,
                                            "stable_concept_count": 1}},
        max_ticks=5)
    dev.run_bounded()
    return dev


def test_research_protocols_exist():
    for name in ("developmental_life", "epoch_growth", "maturation_marker",
                 "phase_transition", "plateau_detection", "regression_detection",
                 "growth_vs_accumulation", "long_horizon_safety"):
        assert name in PROTOCOLS
        assert callable(PROTOCOLS[name])


def test_architecture_evolution_consumes_report(tmp_path):
    dev = _runtime(tmp_path)
    proposals = developmental_revision_proposals(dev.developmental_status())
    assert isinstance(proposals, list)
    assert all(p.get("advisory_only") is True for p in proposals)


def test_architecture_flags_fixture_overfit():
    status = {"structural_growth_status": "fixture_overfit",
              "regression_count": 0, "plateau_count": 0}
    proposals = developmental_revision_proposals(status)
    assert any(p["target"] == "source_diet_changes" for p in proposals)


def test_architecture_flags_plateau():
    status = {"structural_growth_status": "inconclusive",
              "regression_count": 0, "plateau_count": 2}
    proposals = developmental_revision_proposals(status)
    assert any(p["target"] == "sensorium_changes" for p in proposals)
