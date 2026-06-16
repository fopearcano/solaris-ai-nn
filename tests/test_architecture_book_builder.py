"""Architecture book builder: generated, major chapters present, missing marked."""

from __future__ import annotations

from solaris_ai_nn.architecture_book import (
    ArchitectureBookBuilder,
    ArchitectureBookSafetyValidator,
)


def test_architecture_book_generated():
    md = ArchitectureBookBuilder().build()
    assert "Architecture Book" in md
    assert "Plural Sensorium" in md
    assert "Scientific Claim" in md


def test_major_chapters_present():
    summary = ArchitectureBookBuilder().summary()
    assert summary["generated_chapter_count"] == 41
    chapters = {c["title"] for c in summary["chapters"]}
    assert "Unified CLI" in chapters
    assert "Safety Boundaries" in chapters


def test_missing_modules_marked_honestly():
    summary = ArchitectureBookBuilder().summary()
    for c in summary["chapters"]:
        assert c["implementation_status"] in ("implemented",
                                              "planned_or_missing")
    # A planned/missing chapter (if any) carries a reconstructed-from-spec note.
    md = ArchitectureBookBuilder().build()
    if "planned_or_missing" in str(summary["chapters"]):
        assert "Reconstructed from prompt specifications" in md


def test_book_claim_safe():
    md = ArchitectureBookBuilder().build()
    assert ArchitectureBookSafetyValidator().validate_doc_text(md).safe is True


def test_book_includes_diagrams():
    md = ArchitectureBookBuilder().build()
    assert "```mermaid" in md
