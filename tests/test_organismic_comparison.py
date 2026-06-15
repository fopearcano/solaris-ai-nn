"""OrganismicDemoComparison: full vs passive / no-adaptation; negatives kept."""

from __future__ import annotations

from solaris_ai_nn.organismic_demo import (
    OrganismicDemoComparison,
    OrganismicDemoConfig,
)


def _result(tmp_path):
    comp = OrganismicDemoComparison(
        state_dir=str(tmp_path / "cmp"),
        config=OrganismicDemoConfig(ticks=60, seed=7))
    return comp.run()


def test_full_vs_passive_parser(tmp_path):
    result = _result(tmp_path)
    names = {a.name for a in result.arms}
    assert "full" in names and "passive_parser" in names
    full = next(a for a in result.arms if a.name == "full")
    passive = next(a for a in result.arms if a.name == "passive_parser")
    # The passive parser forms no structure; the full system forms some.
    assert passive.metrics["changed_perception_score"] == 0.0
    assert full.metrics["changed_perception_score"] >= \
        passive.metrics["changed_perception_score"]


def test_full_vs_no_adaptation(tmp_path):
    result = _result(tmp_path)
    names = {a.name for a in result.arms}
    assert "no_adaptation" in names


def test_negative_result_preserved(tmp_path):
    result = _result(tmp_path)
    # Whatever the outcome, the negative-result flag is explicit and consistent.
    assert result.negative_result == (not result.full_beats_passive)


def test_no_consciousness_claim(tmp_path):
    result = _result(tmp_path)
    data = result.to_dict()
    assert data["no_consciousness_claim"] is True
    assert "no claim of consciousness" in data["disclaimer"].lower()
