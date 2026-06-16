"""Glossary builder: generated, organismic clarified as metaphor, forbidden clear."""

from __future__ import annotations

from solaris_ai_nn.architecture_book import (
    ArchitectureBookSafetyValidator,
    GlossaryBuilder,
)


def test_glossary_generated():
    entries = GlossaryBuilder().build()
    terms = {e.term for e in entries}
    assert "plural sensorium" in terms
    assert "ClaimGuard" in terms
    assert "Alpha Research System" in terms
    assert len(entries) >= 40


def test_organismic_term_clarified_as_metaphor():
    entries = {e.term: e.definition.lower() for e in GlossaryBuilder().build()}
    assert "metaphor" in entries["organismic substrate"]
    assert "not biological life" in entries["organismic substrate"]


def test_forbidden_claims_clarified():
    entries = {e.term: e.definition.lower() for e in GlossaryBuilder().build()}
    assert "not emotion" in entries["valence"]
    assert "not self-awareness" in entries["self-boundary"] \
        or "not a self" in entries["self-boundary"]
    assert "not agency" in entries["action-reaction"]


def test_glossary_claim_safe():
    md = GlossaryBuilder().render_md()
    assert ArchitectureBookSafetyValidator().validate_doc_text(md).safe is True
