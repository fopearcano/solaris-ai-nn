"""Desire consumes metabolism/cognition/boundary; unsafe boundary inhibits."""

from __future__ import annotations

from solaris_ai_nn.desire_formation import (
    DesireFormationRuntime,
    ValenceSource,
)


def test_consumes_perceptual_needs(tmp_path):
    rt = DesireFormationRuntime(
        state_dir=str(tmp_path / "d"),
        metabolism={"deprivation_state": True, "novelty_appetite_pressure": 0.7,
                    "consolidation_pressure_score": 0.5}, max_ticks=1)
    rt.update(tick=0)
    sources = {v.source for v in rt.valence_assessor.gradient.valences}
    assert ValenceSource.SENSORY_NOVELTY in sources
    assert ValenceSource.CONSOLIDATION_PRESSURE in sources


def test_consumes_question_pressure(tmp_path):
    rt = DesireFormationRuntime(
        state_dir=str(tmp_path / "d"),
        cognition={"failed_prediction_count": 2, "question_pressure_count": 4},
        max_ticks=1)
    rt.update(tick=0)
    sources = {v.source for v in rt.valence_assessor.gradient.valences}
    assert ValenceSource.PREDICTION_FAILURE in sources
    assert ValenceSource.ABSENCE_PRESSURE in sources


def test_consumes_boundary_confidence(tmp_path):
    rt = DesireFormationRuntime(
        state_dir=str(tmp_path / "d"),
        self_boundary={"source_attribution_uncertainty_score": 0.6,
                       "boundary_confidence_score": 0.7}, max_ticks=1)
    rt.update(tick=0)
    sources = {v.source for v in rt.valence_assessor.gradient.valences}
    assert ValenceSource.BOUNDARY_UNCERTAINTY in sources


def test_unsafe_boundary_inhibits_desire(tmp_path):
    # Poor boundary clarity defers desires (does not select internal actions).
    clear = DesireFormationRuntime(
        state_dir=str(tmp_path / "clear"),
        metabolism={"novelty_appetite_pressure": 0.7},
        self_boundary={"boundary_confidence_score": 0.9}, max_ticks=1)
    clear.update(tick=0)
    unclear = DesireFormationRuntime(
        state_dir=str(tmp_path / "unclear"),
        metabolism={"novelty_appetite_pressure": 0.7},
        self_boundary={"boundary_confidence_score": 0.1}, max_ticks=1)
    unclear.update(tick=0)
    assert unclear.desire_status()["deferred_desire_count"] >= \
        clear.desire_status()["deferred_desire_count"]
