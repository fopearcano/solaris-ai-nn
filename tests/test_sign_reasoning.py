"""SignReasoner: sequence/absence inference; correlation not causation."""

from __future__ import annotations

from solaris_ai_nn.semiogenesis import InternalSign, SignKind
from solaris_ai_nn.semiogenesis.private_syntax import (
    PrivateSyntaxPattern,
    SyntaxRelation,
)
from solaris_ai_nn.sensorium_cognition import SignInferenceType, SignReasoner


def _signs():
    return [
        InternalSign(kind=SignKind.MODALITY_NATIVE, sign_code="rf:01",
                     modality_distribution={"radio_frequency": 4}),
        InternalSign(kind=SignKind.MODALITY_NATIVE, sign_code="vib:01",
                     modality_distribution={"vibration": 4}),
    ]


def test_sequence_inference():
    a, b = _signs()
    pat = PrivateSyntaxPattern(relation=SyntaxRelation.SEQUENCE,
                              signs=[a.sign_id, b.sign_id], strength=0.7)
    trace = SignReasoner().reason([a, b], [pat])
    types = {i.inference_type for i in trace.inferences}
    assert SignInferenceType.SEQUENCE in types


def test_absence_inference():
    a, b = _signs()
    pat = PrivateSyntaxPattern(relation=SyntaxRelation.AFTER_ABSENCE,
                              signs=[a.sign_id, b.sign_id], strength=0.4)
    trace = SignReasoner().reason([a, b], [pat])
    types = {i.inference_type for i in trace.inferences}
    assert SignInferenceType.ABSENCE in types


def test_correlation_not_causation():
    a, b = _signs()
    pat = PrivateSyntaxPattern(relation=SyntaxRelation.SEQUENCE,
                              signs=[a.sign_id, b.sign_id], strength=0.7)
    trace = SignReasoner().reason([a, b], [pat])
    assert trace.inferences
    for inf in trace.inferences:
        assert "not causation" in inf.to_dict()["note"]


def test_modality_conflict_inferred():
    a, b = _signs()  # rf vs vibration -> modality conflict
    trace = SignReasoner().reason([a, b], [])
    types = {i.inference_type for i in trace.inferences}
    assert SignInferenceType.MODALITY_CONFLICT in types
