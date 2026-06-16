"""Documentation manifest: serializes, missing visible, contradictory possible."""

from __future__ import annotations

import os

from solaris_ai_nn.architecture_book import (
    DocumentationManifest,
    DocumentationSource,
    DocumentationSourceCategory,
)


def test_manifest_serializes(tmp_path):
    man = DocumentationManifest(state_dir=str(tmp_path))
    man.add_source(DocumentationSource(
        category=DocumentationSourceCategory.README, ref="README.md"))
    d = man.to_dict()
    assert d["documentation_source_count"] == 1
    assert "sources" in d


def test_missing_sources_visible(tmp_path):
    man = DocumentationManifest(state_dir=str(tmp_path))
    man.add_missing("original whitepaper", "not present locally")
    assert len(man.missing()) == 1
    assert man.index()["missing_documentation_source_count"] == 1


def test_contradictory_source_warning_possible(tmp_path):
    man = DocumentationManifest(state_dir=str(tmp_path))
    man.add_source(DocumentationSource(
        category=DocumentationSourceCategory.DOCS, ref="docs/",
        contradictory=True, stale=True))
    assert len(man.contradictory()) == 1
    assert len(man.stale()) == 1


def test_persist_writes_manifest(tmp_path):
    man = DocumentationManifest(state_dir=str(tmp_path))
    man.add_artifact("WHITEPAPER.md", "docs/whitepaper/WHITEPAPER.md")
    path = man.persist_manifest()
    assert os.path.isfile(path)
