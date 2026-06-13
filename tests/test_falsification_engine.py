"""Tests for the falsification engine."""

from __future__ import annotations

from solaris_ai_nn.hypothesis.evidence import EvidenceRecord, EvidenceType
from solaris_ai_nn.hypothesis.falsification import FalsificationEngine
from solaris_ai_nn.hypothesis.hypotheses import Hypothesis, HypothesisType


def _hyp(conf=0.5):
    return Hypothesis(type=HypothesisType.PREDICTION, statement="s",
                      target_ref="t", confidence=conf)


def test_support_updates_confidence():
    engine = FalsificationEngine()
    h = _hyp(0.5)
    ev = EvidenceRecord(hypothesis_id=h.hypothesis_id,
                        evidence_type=EvidenceType.NURSERY_SIMULATED,
                        source_scope="nursery_simulation")
    result = engine.evaluate(h, ev)
    engine.update_confidence(h, result)
    assert result.verdict == "supported"
    assert h.confidence > 0.5
    assert h.status == "supported"


def test_falsifying_lowers_confidence():
    engine = FalsificationEngine()
    h = _hyp(0.5)
    ev = EvidenceRecord(hypothesis_id=h.hypothesis_id,
                        evidence_type=EvidenceType.FALSIFYING,
                        source_scope="nursery_simulation")
    result = engine.evaluate(h, ev)
    engine.update_confidence(h, result)
    assert result.verdict == "falsified"
    assert h.confidence < 0.5
    assert h.status == "falsified"


def test_offline_support_cannot_promote():
    engine = FalsificationEngine()
    h = _hyp(0.5)
    ev = EvidenceRecord(hypothesis_id=h.hypothesis_id,
                        evidence_type=EvidenceType.LATENT_REPLAY,
                        source_scope="latent_replay")
    result = engine.evaluate(h, ev)
    engine.update_confidence(h, result)
    # Offline evidence stays inconclusive and is capped.
    assert result.verdict == "inconclusive"
    assert result.offline_only is True
    assert h.confidence <= engine.offline_confidence_ceiling


def test_inconclusive_handled():
    engine = FalsificationEngine()
    h = _hyp(0.5)
    ev = EvidenceRecord(hypothesis_id=h.hypothesis_id,
                        evidence_type=EvidenceType.INCONCLUSIVE,
                        source_scope="nursery_simulation")
    result = engine.evaluate(h, ev)
    engine.update_confidence(h, result)
    assert result.verdict == "inconclusive"
    assert h.status == "inconclusive"


def test_confidence_change_bounded():
    engine = FalsificationEngine()
    h = _hyp(0.5)
    ev = EvidenceRecord(hypothesis_id=h.hypothesis_id,
                        evidence_type=EvidenceType.OBSERVED_REAL_STREAM,
                        source_scope="read_only_stream_observation")
    result = engine.evaluate(h, ev)
    engine.update_confidence(h, result)
    assert abs(h.confidence - 0.5) <= 0.2
