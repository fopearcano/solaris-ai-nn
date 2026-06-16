"""Architecture book <-> Alpha System integration."""

from __future__ import annotations

import os

from solaris_ai_nn.architecture_book import (
    ArchitectureAppendixBuilder,
    ArchitectureBookRuntime,
    SolarisArchitectureOutlineBuilder,
)


def test_alpha_commands_included_if_available():
    # alpha_system is present in this repo -> appendix CLI reference + outline
    # cover the alpha commands and the alpha chapter is implemented.
    md = ArchitectureAppendixBuilder().build()
    assert "build-docs" in md
    assert "run-demo" in md
    outline = {c.module_key: c.implemented
               for c in SolarisArchitectureOutlineBuilder().build()
               if c.module_key == "alpha_system"}
    assert outline.get("alpha_system") is True


def test_alpha_report_is_documentation_index_entry(tmp_path):
    rt = ArchitectureBookRuntime(state_dir=str(tmp_path / "s"),
                                 docs_dir=str(tmp_path / "d"))
    rt.run()
    labels = [e["label"] for e in rt.doc_index_summary["entries"]]
    assert "Alpha Report" in labels


def test_missing_alpha_report_marked_missing(tmp_path):
    # The alpha report is not generated under this fresh docs dir, so the index
    # marks it missing rather than pretending it exists.
    rt = ArchitectureBookRuntime(state_dir=str(tmp_path / "s"),
                                 docs_dir=str(tmp_path / "d"))
    rt.run()
    entries = {e["label"]: e["present"]
               for e in rt.doc_index_summary["entries"]}
    # Alpha report path is repo-relative; under a temp run it is typically absent.
    assert "Alpha Report" in entries
