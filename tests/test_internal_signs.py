"""InternalSign: serializes; sign_code operational; human_gloss debug-only."""

from __future__ import annotations

from solaris_ai_nn.semiogenesis import (
    InternalSign,
    SignKind,
    operational_sign_code,
)
from solaris_ai_nn.semiogenesis.translation_gloss import GlossStatus


def test_sign_serializes():
    s = InternalSign(kind=SignKind.MODALITY_NATIVE,
                     modality_distribution={"radio_frequency": 4},
                     proto_concept_refs=["C1"])
    d = s.to_dict()
    assert d["kind"] == SignKind.MODALITY_NATIVE
    assert "not a human word" in d["note"]
    assert d["limitations"]


def test_sign_code_operational_not_word():
    code = operational_sign_code("radio_frequency", SignKind.MODALITY_NATIVE)
    assert ":" in code  # compact prefix:suffix operational form
    for human in ("dog", "person", "room", "sentence", "the", "object"):
        assert human != code


def test_sign_auto_generates_code():
    s = InternalSign(kind=SignKind.ABSENCE,
                     modality_distribution={"radio_frequency": 1})
    assert s.sign_code.startswith("abs:")


def test_human_gloss_optional_and_debug_only():
    s = InternalSign(kind=SignKind.MODALITY_NATIVE,
                     modality_distribution={"radio_frequency": 2})
    # By default a sign has no gloss and the gloss status is "not available".
    assert s.human_gloss is None
    assert s.human_gloss_status == GlossStatus.NOT_AVAILABLE
    s.attach_gloss("~approx rf structure", GlossStatus.APPROXIMATE)
    assert s.human_gloss == "~approx rf structure"
    assert s.human_gloss_status == GlossStatus.APPROXIMATE


def test_cross_modal_and_absence_flags():
    cross = InternalSign(kind=SignKind.CROSS_MODAL,
                         modality_distribution={"radio_frequency": 1,
                                                "vibration": 1})
    absent = InternalSign(kind=SignKind.ABSENCE,
                          modality_distribution={"radio_frequency": 1})
    assert cross.is_cross_modal is True
    assert absent.is_absence is True
