"""Chapter model: serializes, evidence refs, claim-safety-blocked possible."""

from __future__ import annotations

from solaris_ai_nn.architecture_book import (
    ArchitectureChapter,
    ChapterEvidenceRef,
    ChapterStatus,
)


def test_chapter_serializes():
    ch = ArchitectureChapter(number="6", title="Plural Sensorium",
                             part="Part II")
    ch.add_section("Purpose", "intake surface")
    d = ch.to_dict()
    assert d["number"] == "6"
    assert d["section_count"] == 1
    assert "Plural Sensorium" in ch.render_md()


def test_evidence_refs_supported():
    ch = ArchitectureChapter(number="6", title="x")
    ch.evidence_refs.append(ChapterEvidenceRef(
        kind="package", ref="solaris_ai_nn.plural_sensorium"))
    assert ch.has_evidence_basis is True


def test_reconstructed_from_spec_is_evidence_basis():
    ch = ArchitectureChapter(number="1", title="What Solaris-AI-NN Is",
                             reconstructed_from_spec=True)
    assert ch.has_evidence_basis is True
    assert "Reconstructed from prompt specifications" in ch.render_md()


def test_claim_safety_blocked_chapter_possible():
    ch = ArchitectureChapter(number="x", title="y",
                             status=ChapterStatus.BLOCKED_BY_CLAIM_SAFETY)
    assert ch.status == ChapterStatus.BLOCKED_BY_CLAIM_SAFETY


def test_limitations_rendered():
    ch = ArchitectureChapter(number="6", title="x",
                             limitations=["fixture-only evidence"])
    assert "Limitations" in ch.render_md()
