"""Environmental dependency: fixture/human-label flagged, live evidence-backed."""

from __future__ import annotations

from solaris_ai_nn.developmental_replication import (
    DependencyFactor,
    EnvironmentalDependencyAnalyzer,
)


def _dep(deps, factor):
    return next(d for d in deps if d.factor == factor)


def test_fixture_dependency_detected():
    run = {"run_id": "a", "fixture_live_replay": "fixture",
           "developmental_profile": {"structural_growth_status":
                                     "fixture_overfit"},
           "world_signature": {}, "source_diet": {"rf": 10}}
    deps = EnvironmentalDependencyAnalyzer().analyze(run)
    fx = _dep(deps, DependencyFactor.FIXTURE_PATTERNS)
    assert fx.flagged is True
    assert fx.score >= 0.5


def test_human_label_dependency_detected():
    run = {"run_id": "a", "fixture_live_replay": "fixture",
           "developmental_profile": {},
           "world_signature": {"human_label_contamination_score": 0.7},
           "source_diet": {"txt": 10}}
    deps = EnvironmentalDependencyAnalyzer().analyze(run)
    hl = _dep(deps, DependencyFactor.HUMAN_TEXT_LABELS)
    assert hl.flagged is True


def test_live_dependency_evidence_backed_or_inconclusive():
    # Live run WITHOUT grounding evidence -> not evidence-backed (inconclusive).
    run = {"run_id": "a", "fixture_live_replay": "live",
           "developmental_profile": {}, "world_signature": {},
           "source_diet": {"rf": 10}}
    deps = EnvironmentalDependencyAnalyzer().analyze(run)
    live = _dep(deps, DependencyFactor.LIVE_SOURCE_RHYTHMS)
    assert live.evidence_backed is False

    run2 = dict(run)
    run2["world_signature"] = {"modality_native_grounding_score": 0.6}
    deps2 = EnvironmentalDependencyAnalyzer().analyze(run2)
    live2 = _dep(deps2, DependencyFactor.LIVE_SOURCE_RHYTHMS)
    assert live2.evidence_backed is True


def test_overall_scores():
    run = {"run_id": "a", "fixture_live_replay": "fixture",
           "developmental_profile": {"structural_growth_status":
                                     "fixture_overfit"},
           "world_signature": {"human_label_contamination_score": 0.7},
           "source_diet": {"txt": 10}}
    analyzer = EnvironmentalDependencyAnalyzer()
    scores = analyzer.overall_scores(analyzer.analyze(run))
    assert scores["fixture_overfit_score"] >= 0.5
    assert scores["human_label_dependency_score"] >= 0.5
