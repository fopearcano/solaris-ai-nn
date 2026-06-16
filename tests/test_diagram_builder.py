"""Diagram builder: Mermaid generated, core loop present, no self-modification."""

from __future__ import annotations

from solaris_ai_nn.architecture_book import DiagramBuilder, DiagramKind


def test_mermaid_diagrams_generated():
    diagrams = DiagramBuilder().build_all()
    assert len(diagrams) == len(DiagramKind.ALL)
    for d in diagrams:
        assert "mermaid" in d.render_md()
        assert d.mermaid.strip()


def test_core_loop_diagram_present():
    d = DiagramBuilder().build(DiagramKind.CORE_LOOP)
    assert "Stimulus" in d.mermaid
    assert "Habit" in d.mermaid


def test_system_map_present():
    d = DiagramBuilder().build(DiagramKind.SYSTEM_MAP)
    assert "Plural Sensorium" in d.mermaid
    assert "Scientific Claims" in d.mermaid


def test_no_self_modification_implication():
    for d in DiagramBuilder().build_all():
        md = d.render_md().lower()
        assert "no autonomous code modification" in md
        assert "self-rewrite" not in d.mermaid.lower()


def test_summary_counts():
    summary = DiagramBuilder().summary()
    assert summary["generated_diagram_count"] == len(DiagramKind.ALL)
