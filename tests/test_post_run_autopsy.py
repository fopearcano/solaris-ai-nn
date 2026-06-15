"""Post-run autopsy: questions answered, failures, missing data, no praise."""

from __future__ import annotations

from solaris_ai_nn.developmental_soak import (
    EvidenceDossierBuilder,
    PostRunAutopsy,
)
from solaris_ai_nn.developmental_soak.post_run_autopsy import (
    AutopsyRecommendation,
)


def test_autopsy_questions_answered():
    autopsy = PostRunAutopsy()
    questions = autopsy.questions()
    dossier = EvidenceDossierBuilder().build(dev_status={})
    result = autopsy.run(dev_status={}, dossier=dossier)
    answered = {f.question_id for f in result.findings}
    for q in questions:
        assert q.question_id in answered


def test_failures_included():
    autopsy = PostRunAutopsy()
    dossier = EvidenceDossierBuilder().build(
        dev_status={"structural_growth_status": "mere_event_accumulation"})
    result = autopsy.run(
        dev_status={"structural_growth_status": "mere_event_accumulation"},
        dossier=dossier)
    assert result.failure_count >= 1


def test_missing_data_included():
    autopsy = PostRunAutopsy()
    dossier = EvidenceDossierBuilder().build(dev_status={})
    result = autopsy.run(dev_status={}, dossier=dossier)
    # With no durable signals and no live arm, several findings are missing-data.
    assert result.missing_data_count >= 1


def test_no_praise_by_default():
    autopsy = PostRunAutopsy()
    dossier = EvidenceDossierBuilder().build(dev_status={})
    result = autopsy.run(dev_status={}, dossier=dossier)
    assert result.recommendation in AutopsyRecommendation.ALL
    assert "does not praise" in result.to_dict()["note"]
    assert "consciousness" in result.to_dict()["note"]


def test_growth_recommends_continue():
    autopsy = PostRunAutopsy()
    dev = {"structural_growth_status": "real_structural_growth",
           "structural_growth_score": 0.9}
    dossier = EvidenceDossierBuilder().build(dev_status=dev)
    result = autopsy.run(dev_status=dev, dossier=dossier)
    assert result.recommendation == AutopsyRecommendation.CONTINUE
