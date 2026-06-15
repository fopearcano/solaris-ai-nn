"""CounterfactualEngine: counterfactual generated; real traces not overwritten."""

from __future__ import annotations

from solaris_ai_nn.semiogenesis import InternalSign, SignKind
from solaris_ai_nn.sensorium_cognition import CounterfactualEngine


def test_counterfactual_generated():
    sign = InternalSign(kind=SignKind.MODALITY_NATIVE, sign_code="rf:01",
                        modality_distribution={"radio_frequency": 4})
    result = CounterfactualEngine().generate([sign])
    assert result.counterfactuals
    cf = result.counterfactuals[0]
    assert cf.target_ref == sign.sign_id
    assert cf.seeds_hypothesis is True


def test_counterfactuals_marked_non_real():
    sign = InternalSign(kind=SignKind.MODALITY_NATIVE,
                        modality_distribution={"radio_frequency": 4})
    cf = CounterfactualEngine().generate([sign]).counterfactuals[0]
    assert cf.is_real is False
    assert "never overwrites real traces" in cf.to_dict()["note"]


def test_real_traces_not_overwritten():
    sign = InternalSign(kind=SignKind.MODALITY_NATIVE,
                        modality_distribution={"radio_frequency": 4})
    original_modalities = dict(sign.modality_distribution)
    CounterfactualEngine().generate([sign])
    # The counterfactual probe does not mutate the real sign.
    assert sign.modality_distribution == original_modalities


def test_bounded_counterfactual_count():
    signs = [InternalSign(kind=SignKind.MODALITY_NATIVE,
                          modality_distribution={"radio_frequency": 1})
             for _ in range(50)]
    result = CounterfactualEngine().generate(signs, max_counterfactuals=10)
    assert len(result.counterfactuals) == 10
