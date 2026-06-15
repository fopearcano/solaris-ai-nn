"""PerceptionChangeProbe: early/late comparison; score; honest null result."""

from __future__ import annotations

from solaris_ai_nn.organismic_demo import (
    MinimalFieldOrganismRunner,
    OrganismicDemoConfig,
    PerceptionChangeProbe,
)


def test_early_late_comparison_works(tmp_path):
    runner = MinimalFieldOrganismRunner(
        state_dir=str(tmp_path / "d"),
        config=OrganismicDemoConfig(ticks=60, seed=7))
    runner.run()
    probe = runner.probe_result
    # At least one probed modality has an early vs late response recorded.
    assert probe.per_modality
    any_mod = next(iter(probe.per_modality.values()))
    assert "sensitivity_delta" in any_mod


def test_changed_perception_score_computed(tmp_path):
    runner = MinimalFieldOrganismRunner(
        state_dir=str(tmp_path / "d"),
        config=OrganismicDemoConfig(ticks=60, seed=7))
    runner.run()
    score = runner.probe_result.changed_perception_score
    assert 0.0 <= score <= 1.0
    # Continuous flux should change at least some response dimensions.
    assert score > 0.0


def test_no_change_reported_honestly():
    # With no responses and an empty runtime-like object, the probe reports a
    # null result rather than inventing change.
    class _Empty:
        class _A:
            events: list = []
        class _Att:
            class state:
                shifts = 0
        class _Inv:
            candidates: dict = {}
        class _XM:
            def relation_count(self):
                return 0
        absence = _A()
        attention = _Att()
        invariants = _Inv()
        cross_modal = _XM()
        proto_symbol_candidates: list = []
        hypotheses: list = []

    result = PerceptionChangeProbe().compute({}, _Empty())
    assert result.changed is False
    assert result.changed_perception_score == 0.0
    assert any("null result" in n.lower() for n in result.notes)


def test_result_disclaims_consciousness(tmp_path):
    runner = MinimalFieldOrganismRunner(
        state_dir=str(tmp_path / "d"),
        config=OrganismicDemoConfig(ticks=40, seed=7))
    runner.run()
    blob = str(runner.probe_result.to_dict()).lower()
    assert "not consciousness" in blob
