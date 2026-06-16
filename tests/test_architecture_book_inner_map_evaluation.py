"""Architecture book <-> Inner MAP + Evaluation integration."""

from __future__ import annotations

import tempfile

import pytest

from solaris_ai_nn.architecture_book import ArchitectureBookRuntime
from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS
from solaris_ai_nn.inner_map.observer import InnerMapObserver

_NAMES = (
    "architecture_book", "documentation_manifest_protocol",
    "source_collection_protocol", "whitepaper_generation_protocol",
    "architecture_book_generation_protocol", "diagram_generation_protocol",
    "glossary_generation_protocol", "documentation_safety",
)


def test_inner_map_includes_documentation_state(tmp_path):
    rt = ArchitectureBookRuntime(state_dir=str(tmp_path / "s"),
                                 docs_dir=str(tmp_path / "d"))
    rt.run()
    model = InnerMapObserver(architecture_book=rt).update()
    assert model.architecture_book is not None
    assert model.architecture_book["architecture_book_enabled"] is True
    assert model.architecture_book["published"] is False
    assert "architecture_book" in model.to_dict()


def test_inner_map_warning_when_unavailable():
    model = InnerMapObserver().update()
    assert model.architecture_book is None


def test_metrics_computed():
    metrics = M.architecture_book_metrics({
        "documentation_source_count": 14, "generated_document_count": 9,
        "generated_chapter_count": 41, "generated_diagram_count": 10})
    assert metrics["present"] is True
    assert metrics["generated_document_count"] == 9
    assert metrics["is_consciousness_or_personhood"] is False


def test_metrics_absent():
    assert M.architecture_book_metrics(None)["present"] is False


@pytest.mark.parametrize("name", _NAMES)
def test_protocols_return_results(name):
    r = ExperimentRegistry()
    m = r.build_manifest("architecture_book", {"state_dir": tempfile.mkdtemp()})
    result = PROTOCOLS[name](m)
    assert result.success, result.error
    assert "architecture_book" in result.metrics


def test_feature_flag_set():
    r = ExperimentRegistry()
    m = r.build_manifest("architecture_book")
    assert m.enabled_features.get("architecture_book") is True
