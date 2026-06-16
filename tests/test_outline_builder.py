"""Outline builder: all parts present, prompts 41-66 represented, no life claim."""

from __future__ import annotations

from solaris_ai_nn.architecture_book import SolarisArchitectureOutlineBuilder


def test_outline_contains_all_major_parts():
    parts = SolarisArchitectureOutlineBuilder().parts()
    assert len(parts) == 7
    assert any("Project Frame" in p for p in parts)
    assert any("Organismic Substrate" in p for p in parts)
    assert any("Safety" in p for p in parts)


def test_chapter_count_is_41():
    summary = SolarisArchitectureOutlineBuilder().summary()
    assert summary["outline_chapter_count"] == 41


def test_prompts_41_66_represented():
    chapters = SolarisArchitectureOutlineBuilder().build()
    titles = " ".join(c.title for c in chapters).lower()
    # Spot-check coverage across prompt ranges.
    assert "plural sensorium" in titles
    assert "scientific claim" in titles
    assert "independent review" in titles
    assert "unified cli" in titles
    assert "appendices" in titles


def test_no_biological_life_claim():
    md = SolarisArchitectureOutlineBuilder().render_md()
    assert "metaphor" in md.lower()
    assert "biological life" not in md.lower() or "no claim of biological life" \
        in md.lower()


def test_implementation_status_marked():
    chapters = SolarisArchitectureOutlineBuilder().build()
    for c in chapters:
        d = c.to_dict()
        assert d["implementation_status"] in ("implemented",
                                              "planned_or_missing")
