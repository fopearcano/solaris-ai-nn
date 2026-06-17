"""Live contamination filter: operator/human-label/gloss dependence; blocks birth."""

from __future__ import annotations

from solaris_ai_nn.live_ontogenesis import (
    LiveFeatureVector,
    LiveOntogenesisContaminationFilter,
    LiveProtoConceptCandidate,
)


def _cand(cid, sources):
    c = LiveProtoConceptCandidate(candidate_id=cid, feature_signature="s")
    c.source_distribution = dict(sources)
    c.recurrence_count = sum(sources.values())
    for i, (src, n) in enumerate(sources.items()):
        for j in range(n):
            c.add_support(f"{cid}_{src}_{j}", src, "")
    return c


def _vec(event_id, source_id, label_gt=False, gloss_gt=False, scalar=False):
    return LiveFeatureVector(
        event_id=event_id, source_id=source_id, modality="scalar", channel="c",
        scalar_values={"v": "<= 1.0"} if scalar else {},
        attempted_human_label_ground_truth=label_gt,
        attempted_debug_gloss_ground_truth=gloss_gt)


def test_operator_dominance_detected():
    c = _cand("c1", {"operator_pulse": 5})
    vecs = {f"c1_operator_pulse_{j}": _vec(f"c1_operator_pulse_{j}",
                                           "operator_pulse") for j in range(5)}
    res = LiveOntogenesisContaminationFilter().evaluate(
        candidate=c, vectors_by_event=vecs, source_diet={})
    types = {f["contamination_type"] for f in res.to_dict()["findings"]}
    assert "operator_pulse_dominance" in types
    assert res.contaminated is True


def test_human_label_dependence_detected():
    c = _cand("c2", {"machine_body": 3})
    vecs = {f"c2_machine_body_{j}": _vec(f"c2_machine_body_{j}", "machine_body",
                                         label_gt=(j == 0)) for j in range(3)}
    res = LiveOntogenesisContaminationFilter().evaluate(
        candidate=c, vectors_by_event=vecs, source_diet={})
    types = {f["contamination_type"] for f in res.to_dict()["findings"]}
    assert "human_label_ground_truth_attempt" in types


def test_debug_gloss_dependence_detected():
    c = _cand("c3", {"machine_body": 3})
    vecs = {f"c3_machine_body_{j}": _vec(f"c3_machine_body_{j}", "machine_body",
                                         gloss_gt=(j == 0)) for j in range(3)}
    res = LiveOntogenesisContaminationFilter().evaluate(
        candidate=c, vectors_by_event=vecs, source_diet={})
    types = {f["contamination_type"] for f in res.to_dict()["findings"]}
    assert "debug_gloss_ground_truth_attempt" in types


def test_contaminated_candidate_blocks_birth():
    c = _cand("c4", {"operator_pulse": 5})
    vecs = {f"c4_operator_pulse_{j}": _vec(f"c4_operator_pulse_{j}",
                                           "operator_pulse") for j in range(5)}
    res = LiveOntogenesisContaminationFilter().evaluate(
        candidate=c, vectors_by_event=vecs, source_diet={})
    assert res.contaminated is True
    assert any(f.blocks_birth for f in res.findings)
