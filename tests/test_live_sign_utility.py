"""Live sign utility: useful sign higher; label-dependent downgraded; missing low."""

from __future__ import annotations

from solaris_ai_nn.live_semiogenesis import (
    LiveSignCandidate,
    LiveSignUtilityAssessment,
)


def _cand(sid, sources, contamination=None, refs=("sig:c",)):
    c = LiveSignCandidate(sign_id=sid, private_token=f"sig_live_{sid}",
                          linked_concept_ids=["c"],
                          feature_signature_refs=list(refs))
    c.source_distribution = dict(sources)
    c.modality_distribution = {"scalar": sum(sources.values())}
    c.contamination_findings = contamination or []
    c.add_support("c", kind="concept")
    return c


def test_useful_sign_scores_higher():
    useful = LiveSignUtilityAssessment().assess(
        candidate=_cand("ok", {"machine_body": 6}), concept_stability=0.72,
        concept_recurrence=6)
    label = LiveSignUtilityAssessment().assess(
        candidate=_cand("lbl", {"operator_pulse": 5},
                        contamination=["human_label_copy"]),
        concept_stability=0.6, concept_recurrence=5)
    assert useful.score > label.score
    assert useful.useful is True


def test_label_dependent_downgraded():
    s = LiveSignUtilityAssessment().assess(
        candidate=_cand("lbl", {"machine_body": 5},
                        contamination=["human_label_copy"]),
        concept_stability=0.7, concept_recurrence=5)
    assert s.score < 0.6
    assert any("label" in n for n in s.notes)


def test_missing_evidence_lowers_confidence():
    s = LiveSignUtilityAssessment().assess(
        candidate=_cand("thin", {"machine_body": 1}, refs=()),
        concept_stability=0.3, concept_recurrence=1)
    assert s.score < 0.6
    assert any("recurrence" in n for n in s.notes)
