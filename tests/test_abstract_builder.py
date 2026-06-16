"""Abstract builder: safe abstract, weak evidence stated, no forbidden claim."""

from __future__ import annotations

from solaris_ai_nn.scientific_claims import (
    AbstractVariant,
    ScientificAbstractBuilder,
)


def test_safe_abstract_generated():
    builder = ScientificAbstractBuilder()
    text = builder.build(AbstractVariant.TECHNICAL_PREPRINT,
                         supported_claims=[{"text": "signs form"}])
    assert "Technical Preprint" in text
    assert builder.check_safety(text).safe is True


def test_weak_evidence_stated():
    builder = ScientificAbstractBuilder()
    text = builder.build(AbstractVariant.INTERNAL_RESEARCH_SUMMARY,
                         weak_claims=[{"text": "weakly observed"}])
    assert "weakly supported" in text.lower()


def test_no_publishable_claim_falls_back():
    builder = ScientificAbstractBuilder()
    text = builder.build(AbstractVariant.TECHNICAL_PREPRINT,
                         negative_results=[{"text": "did not emerge"}])
    assert "Negative-Result" in text or "Inconclusive-Result" in text


def test_forbidden_claim_absent():
    builder = ScientificAbstractBuilder()
    text = builder.build(AbstractVariant.README_SAFE_SUMMARY,
                         supported_claims=[{"text": "structures form"}])
    # The mandatory disclaimer is present and no forbidden claim is asserted.
    assert "makes no claim of consciousness" in text
    assert builder.check_safety(text).safe is True


def test_build_all_variants():
    abstracts = ScientificAbstractBuilder().build_all(
        supported_claims=[{"text": "x"}])
    for v in AbstractVariant.ALL:
        assert v in abstracts and abstracts[v]
