"""Appendix builder: generated, prompt roadmap, artifact mapping included."""

from __future__ import annotations

from solaris_ai_nn.architecture_book import (
    ArchitectureAppendixBuilder,
    ArchitectureBookSafetyValidator,
)


def test_appendices_generated():
    md = ArchitectureAppendixBuilder().build()
    assert "Appendices" in md
    assert "Appendix A" in md
    assert "Appendix H" in md


def test_prompt_roadmap_included():
    md = ArchitectureAppendixBuilder().build()
    assert "Prompt Roadmap" in md
    assert "41" in md and "66" in md
    assert "plural_sensorium" in md
    assert "architecture_book" in md


def test_artifact_mapping_included():
    md = ArchitectureAppendixBuilder().build()
    assert "Artifact Directory Mapping" in md
    assert ".solaris_ai_nn_alpha" in md
    assert ".solaris_ai_nn_claims" in md


def test_forbidden_and_cli_index_included():
    md = ArchitectureAppendixBuilder().build()
    assert "Forbidden Claim Index" in md
    assert "CLI Command Reference" in md
    assert "build-docs" in md


def test_appendices_claim_safe():
    md = ArchitectureAppendixBuilder().build()
    assert ArchitectureBookSafetyValidator().validate_doc_text(md).safe is True
