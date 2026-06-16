"""Source collector: local docs collected, missing dirs warn, no execution."""

from __future__ import annotations

import inspect

from solaris_ai_nn.architecture_book import ArchitectureSourceCollector


def test_local_docs_collected():
    result = ArchitectureSourceCollector().collect()
    labels = {s.label for s in result.sources}
    assert "readme" in labels or "docs" in labels
    # The package module list should be populated in this repo.
    assert result.package_modules


def test_missing_dirs_warn(tmp_path):
    # A repo root with no state dirs -> warnings, not failures.
    collector = ArchitectureSourceCollector(repo_root=str(tmp_path))
    result = collector.collect()
    assert result.warnings
    assert result.missing()


def test_no_command_execution():
    src = inspect.getsource(ArchitectureSourceCollector)
    assert "subprocess" not in src
    assert "os.system" not in src
    assert "eval(" not in src


def test_collection_serializes():
    d = ArchitectureSourceCollector().collect().to_dict()
    assert "collected_source_count" in d
    assert "note" in d
