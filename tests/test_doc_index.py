"""Documentation index: generated, missing docs visible."""

from __future__ import annotations

import os

from solaris_ai_nn.architecture_book import DocumentationIndexBuilder


def test_docs_index_generated(tmp_path):
    # An empty docs dir -> all whitepaper docs missing, listed honestly.
    index = DocumentationIndexBuilder(docs_dir=str(tmp_path)).build()
    d = index.to_dict()
    assert d["documentation_index_entry_count"] >= 9
    assert "Whitepaper" in " ".join(e["label"] for e in d["entries"])


def test_missing_docs_visible(tmp_path):
    index = DocumentationIndexBuilder(docs_dir=str(tmp_path)).build()
    assert index.missing()  # nothing written yet -> all whitepaper docs missing
    md = index.render_md()
    assert "Missing documents" in md


def test_present_docs_detected(tmp_path):
    # Write one doc and confirm it is detected as present.
    path = os.path.join(str(tmp_path), "SOLARIS_AI_NN_WHITEPAPER.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# wp")
    index = DocumentationIndexBuilder(docs_dir=str(tmp_path)).build()
    present_labels = {e["label"] for e in index.present()}
    assert "Technical Whitepaper" in present_labels
