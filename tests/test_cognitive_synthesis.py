"""SynthesisEngine: merge/split/preserve; fragments preserved; contradiction kept."""

from __future__ import annotations

from solaris_ai_nn.semiogenesis import InternalSign, SignKind
from solaris_ai_nn.sensorium_cognition import SynthesisEngine, SynthesisOp
from solaris_ai_nn.sensorium_cognition.sign_reasoning import (
    SignInferenceType,
    SignRelationInference,
)


def _signs():
    rf = InternalSign(kind=SignKind.MODALITY_NATIVE, sign_code="rf:01",
                      modality_distribution={"radio_frequency": 4})
    vib = InternalSign(kind=SignKind.MODALITY_NATIVE, sign_code="vib:01",
                       modality_distribution={"vibration": 4})
    ambiguous = InternalSign(kind=SignKind.MODALITY_NATIVE, sign_code="echo:01",
                             modality_distribution={"alien_echo": 2})
    ambiguous.ambiguity_score = 0.7
    return rf, vib, ambiguous


def test_merge_split_preserve_tension():
    rf, vib, ambiguous = _signs()
    inferences = [
        SignRelationInference(
            inference_type=SignInferenceType.CROSS_MODAL_UNITY,
            sign_refs=[rf.sign_id, vib.sign_id], confidence=0.6),
        SignRelationInference(
            inference_type=SignInferenceType.CONTRADICTION,
            sign_refs=[rf.sign_id, vib.sign_id], confidence=0.4),
    ]
    synthesis = SynthesisEngine().synthesize([rf, vib, ambiguous], inferences)
    ops = {r.op for r in synthesis.results}
    assert SynthesisOp.MERGE_CROSS_MODAL in ops
    assert SynthesisOp.SPLIT_AMBIGUOUS in ops
    assert SynthesisOp.PRESERVE_CONTRADICTION in ops


def test_fragments_preserved():
    rf, vib, _ = _signs()
    inf = SignRelationInference(
        inference_type=SignInferenceType.CROSS_MODAL_UNITY,
        sign_refs=[rf.sign_id, vib.sign_id], confidence=0.6)
    synthesis = SynthesisEngine().synthesize([rf, vib], [inf])
    merge = [r for r in synthesis.results
             if r.op == SynthesisOp.MERGE_CROSS_MODAL][0]
    # The merged fragments are recorded, not deleted.
    assert rf.sign_id in merge.fragment_refs
    assert vib.sign_id in merge.fragment_refs


def test_contradiction_remains_visible():
    rf, vib, _ = _signs()
    inf = SignRelationInference(
        inference_type=SignInferenceType.CONTRADICTION,
        sign_refs=[rf.sign_id, vib.sign_id], confidence=0.4)
    synthesis = SynthesisEngine().synthesize([rf, vib], [inf])
    preserved = [r for r in synthesis.results if r.preserved_contradiction]
    assert preserved
    assert "irreducible contradiction stays visible" in \
        preserved[0].to_dict()["note"]
