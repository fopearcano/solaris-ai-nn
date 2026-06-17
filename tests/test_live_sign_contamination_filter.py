"""Live sign contamination filter: label/gloss/operator copy + secret blocked."""

from __future__ import annotations

from solaris_ai_nn.live_semiogenesis import (
    LiveSignCandidate,
    LiveSignContaminationFilter,
)


def _cand(sid, token, sources, alias="", contamination=None):
    c = LiveSignCandidate(sign_id=sid, private_token=token,
                          linked_concept_ids=["c"])
    c.source_distribution = dict(sources)
    c.debug_alias = alias
    c.contamination_findings = contamination or []
    return c


def test_human_label_copy_detected():
    c = _cand("s1", "the calm machine", {"machine_body": 5})
    res = LiveSignContaminationFilter().evaluate(candidate=c)
    assert "human_label_copy" in res.types


def test_debug_gloss_copy_detected():
    c = _cand("s2", "sig_live_abc", {"machine_body": 5},
              contamination=["debug_gloss_copy"])
    res = LiveSignContaminationFilter().evaluate(candidate=c)
    assert "debug_gloss_copy" in res.types


def test_operator_phrase_copy_and_dominance_detected():
    c = _cand("s3", "sig_live_abc", {"operator_pulse": 5})
    res = LiveSignContaminationFilter().evaluate(candidate=c)
    assert "operator_pulse_dominance" in res.types
    assert res.contaminated is True


def test_secret_marker_blocked():
    c = _cand("s4", "api_key=hunter2", {"machine_body": 5})
    res = LiveSignContaminationFilter().evaluate(candidate=c)
    assert "secret_marker" in res.types
    assert res.contaminated is True
